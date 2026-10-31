---
id: "020"
title: "Empirically Probe Host Hardware and Align Manuscript Specifications"
type: "docs"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Docs] Empirically Probe Host Hardware and Align Manuscript Specifications

## Description
Empirically probe host workstation hardware (CPU, physical RAM, NVMe SSD model and capacity, Linux kernel, and chassis vendor) via concrete system commands and ground all manuscript sections (`paper/sections/*.tex`) with the empirical reality of the testbed machine (ASUS VivoBook 15 X513EA, Intel Core i5-1135G7, 8 GB DDR4, Micron 2210 512 GB PCIe 3.0 NVMe SSD, Ubuntu 26.04.1 LTS).

## Acceptance Criteria
- [x] Empirically probe host hardware using `/proc`, `/sys`, `lscpu`, `udevadm`, `lsblk`, and `/etc/os-release`.
- [x] Update `paper/sections/04_experimental_setup.tex` Section 4.1 with verified hardware specifications: ASUS VivoBook 15 (X513EA), Intel Core i5-1135G7 (4 cores, 8 threads, 8 MiB L3 cache, 2.40 GHz base, up to 4.20 GHz boost), 8 GB DDR4 RAM (7.0 GiB addressable), Micron 2210 512 GB PCIe 3.0 NVMe SSD (up to 2,200 MB/s read, 1,070 MB/s write), and Ubuntu 26.04.1 LTS.
- [x] Update `paper/sections/01_introduction.tex` and `paper/sections/05_results_and_discussion.tex` to remove fabricated references to 16 GB RAM baseline and PCIe 4.0 storage, accurately reflecting physical 8 GB RAM (7.0 GiB addressable) and PCIe 3.0 NVMe spilling.
- [x] Recompile `paper/main.pdf` using Tectonic with zero typesetting errors.
- [x] Verify test suite `./tests/scripts/sh/test.sh` passes 100% green inside Docker container.

## Context / Notes
- Target files: `paper/sections/04_experimental_setup.tex`, `paper/sections/01_introduction.tex`, `paper/sections/05_results_and_discussion.tex`, `paper/main.pdf`
- Empirical Grounding: ASUS VivoBook 15 X513EA, Intel Core i5-1135G7, 8 GB RAM (7.0 GiB usable), Micron 2210 MTFDHBA512QFD 512 GB NVMe SSD, Ubuntu 26.04.1 LTS.
