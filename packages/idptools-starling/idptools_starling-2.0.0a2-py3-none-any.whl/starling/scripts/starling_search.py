#!/usr/bin/env python
"""
starling_search CLI
Usage:
  starling_search build --root ROOT --index INDEX.faiss --tokens TOKENS_DIR [options]
  starling_search query [--index INDEX.faiss|default] --metric cosine --seq SEQ [--seq SEQ ...] [options]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from typing import List, Optional

import protfasta
import torch

from starling.configs import ensure_search_artifacts
from starling.search import IndexBuilder, SearchEngine


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="starling_search",
        description=(
            "starling_search: build and query FAISS indexes for protein sequence similarity.\n\n"
            "Commands:\n"
            "  build   Build a FAISS index from pretokenized sequence data.\n"
            "  query   Query a FAISS index with one or more sequences and return nearest neighbors.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Build an index:\n"
            "    starling_search build --root /data/starling --tokens /data/tokens --index myindex.faiss\n\n"
            "  Query the index:\n"
            "    starling_search query --index myindex.faiss --seq MKT... --seq HLL... --k 20\n\n"
            "Notes:\n"
            "  - Use 'starling-pretokenize' to create the tokens directory required by 'build'.\n"
            "  - Passing --index default or a missing path will attempt to fetch/cache the default index.\n"
            "  - See individual command flags for advanced options (metric, GPU usage, reranking, output format).\n"
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser(
        "build",
        help="Build a FAISS index from custom tokenized data - see 'starling-pretokenize' for tokenization",
    )
    b.add_argument("--root", required=True)
    b.add_argument("--index", required=True)
    b.add_argument("--tokens", required=True)
    b.add_argument("--metric", choices=["cosine", "l2"], default="cosine")
    b.add_argument("--sample-size", type=int, default=655360)
    b.add_argument("--nlist", type=int, default=16384)
    b.add_argument("--m", type=int, default=64)
    b.add_argument("--nbits", type=int, default=8)
    b.add_argument("--add-batch-size", type=int, default=100000)
    b.add_argument("--nprobe", type=int, default=16)
    b.add_argument("--use-gpu", action="store_false")
    b.add_argument("--gpu-device", type=int, default=0)
    b.add_argument("--gpu-fp16-lut", action="store_false")
    b.add_argument("--opq", action="store_true")
    b.add_argument("--compress", action="store_true")
    b.add_argument("--shard-regex", default=None)
    b.add_argument("--verbose", action="store_false")

    q = sub.add_parser("query", help="Command to query a built FAISS index")
    q.add_argument(
        "--index",
        default="default",
        help="Path to a FAISS index (default: 'default' to auto-fetch/cache)",
    )
    q.add_argument("--metric", choices=["cosine", "l2"], default="cosine")
    q.add_argument("--seq", nargs="*", default=None, help="Sequences")
    q.add_argument("--k", type=int, default=10)
    q.add_argument("--nprobe", type=int, default=64)
    q.add_argument("--return-sim", action="store_false")
    q.add_argument("--exclude-exact", action="store_false")
    q.add_argument("--sequence-identity-max", type=float, default=None)
    q.add_argument(
        "--identity-denominator",
        choices=["query", "target", "max", "min", "avg"],
        default="query",
    )
    q.add_argument("--device", default="cuda:0")
    q.add_argument("--batch-size", type=int, default=256)
    q.add_argument("--ionic-strength", type=int, default=150)
    q.add_argument("--max-cosine-similarity", type=float, default=None)
    q.add_argument("--min-l2-distance", type=float, default=None)
    q.add_argument("--length-min", type=int, default=None)
    q.add_argument("--length-max", type=int, default=None)
    q.add_argument("--rerank", action="store_false")
    q.add_argument("--rerank-batch-size", type=int, default=64)
    q.add_argument("--rerank-device", type=str, default=None)
    q.add_argument("--rerank-ionic-strength", type=int, default=None)
    q.add_argument(
        "--out",
        default="nearest_neighbors",
        help="Output file basename (extension auto-set to .csv or .jsonl; any provided extension will be replaced)",
    )
    q.add_argument("--out-format", choices=["csv", "jsonl"], default="csv")
    q.add_argument("--verbose", action="store_false")
    return p.parse_args(argv)


def _write(
    path: str,
    fmt: str,
    queries: List[str],
    results,
    engine: SearchEngine,
    return_similarity: bool,
    metric: str,
):
    all_gids = [gid for row in results for _, gid, _, _ in row]
    gid_to_header_len = {}
    if engine.seq_store:
        for g, h, length_val in engine.seq_store.get_many_header_len(all_gids):
            gid_to_header_len[int(g)] = (h, length_val)

    def get_seq(gid: int):
        return engine.seq_store.get_seq(int(gid)) if engine.seq_store else None

    if fmt == "csv":
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "query_index",
                    "query_seq",
                    "rank",
                    "gid",
                    "score",
                    "similarity",
                    "header",
                    "length",
                    "sequence",
                ]
            )
            for qi in range(len(results)):
                qseq = queries[qi] if qi < len(queries) else ""
                for rank, (score, gid, _, _) in enumerate(results[qi]):
                    if metric == "cosine" and return_similarity:
                        sim = score
                        out_score = 1.0 - sim
                    elif metric == "cosine":
                        out_score = score
                        sim = 1.0 - out_score
                    else:
                        out_score = score
                        sim = ""
                    h, L = gid_to_header_len.get(int(gid), (None, None))
                    seq = get_seq(int(gid))
                    w.writerow([qi, qseq, rank, int(gid), out_score, sim, h, L, seq])
    else:
        with open(path, "w") as f:
            for qi in range(len(results)):
                qseq = queries[qi] if qi < len(queries) else ""
                for rank, (score, gid, _, _) in enumerate(results[qi]):
                    if metric == "cosine" and return_similarity:
                        sim = score
                        out_score = 1.0 - sim
                    elif metric == "cosine":
                        out_score = score
                        sim = 1.0 - out_score
                    else:
                        out_score = score
                        sim = None
                    h, L = gid_to_header_len.get(int(gid), (None, None))
                    obj = {
                        "query_index": qi,
                        "query_seq": qseq,
                        "rank": rank,
                        "gid": int(gid),
                        "score": out_score,
                        "similarity": sim,
                        "header": h,
                        "length": L,
                        "sequence": get_seq(int(gid)),
                    }
                    f.write(json.dumps(obj) + "\n")


def _write_fasta(
    path_base: str,
    queries: List[str],
    results,
    engine: SearchEngine,
    return_similarity: bool,
    metric: str,
):
    """Write FASTA of hits using protfasta.write_fasta."""
    fasta_path = path_base + ".fasta"
    all_gids = [gid for row in results for _, gid, _, _ in row]
    gid_to_header_len = {}
    if engine.seq_store:
        for g, h, length_val in engine.seq_store.get_many_header_len(all_gids):
            gid_to_header_len[int(g)] = (h, length_val)

    def get_seq(gid: int):
        return engine.seq_store.get_seq(int(gid)) if engine.seq_store else None

    entries = []  # list of [header, sequence]
    for qi in range(len(results)):
        for rank, (score, gid, _, _) in enumerate(results[qi]):
            if metric == "cosine" and return_similarity:
                sim = score
                out_score = 1.0 - sim
            elif metric == "cosine":
                out_score = score
                sim = 1.0 - out_score
            else:
                out_score = score
                sim = None
            db_header, length_val = gid_to_header_len.get(int(gid), (None, None))
            seq = get_seq(int(gid))
            if not seq:
                continue
            safe_db_header = (db_header or "").replace(" ", "_")[:200]
            parts = [
                f"q{qi}",
                f"rank={rank}",
                f"gid={int(gid)}",
                f"score={out_score:.6f}",
            ]
            if metric == "cosine":
                parts.append(f"similarity={(sim if sim is not None else 0):.6f}")
            if length_val is not None:
                parts.append(f"length={length_val}")
            if safe_db_header:
                parts.append(f"db_header={safe_db_header}")
            header = "|".join(parts)
            entries.append([header, seq])
    protfasta.write_fasta(entries, fasta_path, linelength=80)
    print(f"wrote {fasta_path}")


def main(argv: Optional[List[str]] = None) -> int:
    a = parse_args(argv)
    if a.cmd == "build":
        builder = IndexBuilder(
            root=a.root,
            metric=a.metric,
            verbose=a.verbose,
            shard_id_regex=a.shard_regex,
        )
        builder.build_index(
            index_path=a.index,
            sample_size=a.sample_size,
            nlist=a.nlist,
            m=a.m,
            nbits=a.nbits,
            use_gpu=a.use_gpu,
            add_batch_size=a.add_batch_size,
            nprobe=a.nprobe,
            gpu_device=a.gpu_device,
            gpu_fp16_lut=a.gpu_fp16_lut,
            tokens_dir=a.tokens,
            compress_sequences=a.compress,
            use_opq=a.opq,
        )
        print("[done]")
        return 0
    if a.cmd == "query":
        # Fallback: if user passes 'default' or file missing, attempt auto-download/cache
        missing = not os.path.exists(a.index)
        if a.index == "default" or missing:
            idx_path, _, _ = ensure_search_artifacts(download=True)
            if missing and a.index != "default":
                print(
                    f"[search] Index '{a.index}' not found; using cached default '{idx_path}'"
                )
            elif a.index == "default":
                print(f"[search] Using default cached index '{idx_path}'")
            a.index = idx_path
        engine = SearchEngine.load(
            index_path=a.index, metric=a.metric, verbose=a.verbose
        )
        seqs = [s for s in (a.seq or []) if s]
        if not seqs:
            print("no sequences")
            return 0
        from starling.inference.generation import sequence_encoder_backend

        seq_dict = {f"q{i}": s for i, s in enumerate(seqs)}
        embs = sequence_encoder_backend(
            sequence_dict=seq_dict,
            device=a.device,
            batch_size=a.batch_size,
            ionic_strength=a.ionic_strength,
            aggregate=True,
            output_directory=None,
        )
        names = [f"q{i}" for i in range(len(seqs))]
        qvecs = torch.stack([embs[n] for n in names]).float()
        if engine.metric == "cosine":
            qvecs = torch.nn.functional.normalize(qvecs, dim=1)
        res = engine.search(
            queries=qvecs,
            k=a.k,
            nprobe=a.nprobe,
            return_similarity=a.return_sim,
            query_sequences=seqs,
            exclude_exact=a.exclude_exact,
            sequence_identity_max=a.sequence_identity_max,
            identity_denominator=a.identity_denominator,
            max_cosine_similarity=a.max_cosine_similarity,
            min_l2_distance=a.min_l2_distance,
            length_min=a.length_min,
            length_max=a.length_max,
            rerank=a.rerank,
            rerank_batch_size=a.rerank_batch_size,
            rerank_device=a.rerank_device or a.device,
            rerank_ionic_strength=a.rerank_ionic_strength,
        )
        if a.out:
            base, _old_ext = os.path.splitext(a.out)
            if not base:  # edge case like '.results'
                base = a.out.lstrip(".") or "output"
            out_path = base + (".csv" if a.out_format == "csv" else ".jsonl")
            _write(out_path, a.out_format, seqs, res, engine, a.return_sim, a.metric)
            _write_fasta(base, seqs, res, engine, a.return_sim, a.metric)
            print(f"wrote {out_path}")
        else:
            for qi, row in enumerate(res):
                print(f"q{qi} {seqs[qi]} -> {len(row)} hits")
                for score, gid, header, length in row[:5]:
                    print(f"  {gid}\t{score:.4f}\t{length}\t{header}")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
