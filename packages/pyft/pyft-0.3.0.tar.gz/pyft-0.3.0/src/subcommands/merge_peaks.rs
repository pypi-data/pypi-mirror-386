use crate::utils::bio_io;
use anyhow::*;
use rust_lapper::{Interval, Lapper};
use std::io::BufRead;
use std::collections::HashMap;

// Use u32 for genomic coordinates to match most genomic formats
type Position = u32;

#[derive(Debug, Clone)]
pub struct BedEntry {
    pub chrom: String,
    pub start: Position,
    pub end: Position,
    pub extra_fields: Vec<String>,
}

impl BedEntry {
    pub fn length(&self) -> Position {
        self.end - self.start
    }

    pub fn to_interval(&self, id: usize) -> Interval<Position, usize> {
        Interval {
            start: self.start,
            stop: self.end,
            val: id,
        }
    }
}

#[derive(Debug)]
pub struct OverlapResult {
    pub entry1: BedEntry,
    pub entry2: BedEntry,
    pub overlap_length: Position,
    pub overlap_fraction1: f64,  // fraction of entry1 that overlaps
    pub overlap_fraction2: f64,  // fraction of entry2 that overlaps
}

pub struct BedOverlapTool {
    pub bed1_entries: Vec<BedEntry>,
    pub bed2_entries: Vec<BedEntry>,
    pub lappers: HashMap<String, Lapper<Position, usize>>,
}

impl BedOverlapTool {
    pub fn new() -> Self {
        BedOverlapTool {
            bed1_entries: Vec::new(),
            bed2_entries: Vec::new(),
            lappers: HashMap::new(),
        }
    }

    pub fn load_bed_file(path: &str) -> anyhow::Result<Vec<BedEntry>> {
        let reader = bio_io::buffer_from(path)?;
        let mut entries = Vec::new();

        for line_result in reader.lines() {
            let line = line_result?;
            let line = line.trim();

            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            let fields: Vec<&str> = line.split('\t').collect();
            if fields.len() < 3 {
                return Err(anyhow!("Invalid BED format: line has fewer than 3 fields"));
            }

            let entry = BedEntry {
                chrom: fields[0].to_string(),
                start: fields[1].parse()?,
                end: fields[2].parse()?,
                extra_fields: if fields.len() > 3 {
                    fields[3..].iter().map(|s| s.to_string()).collect()
                } else {
                    Vec::new()
                },
            };

            entries.push(entry);
        }

        Ok(entries)
    }

    pub fn load_bed1(&mut self, path: &str) -> anyhow::Result<()> {
        self.bed1_entries = Self::load_bed_file(path)?;
        Ok(())
    }

    pub fn load_bed2(&mut self, path: &str) -> anyhow::Result<()> {
        self.bed2_entries = Self::load_bed_file(path)?;
        Ok(())
    }

    pub fn build_lapper_from_bed1(&mut self) {
        // Group bed1 entries by chromosome and build lappers
        let mut chrom_intervals: HashMap<String, Vec<Interval<Position, usize>>> = HashMap::new();

        for (i, entry) in self.bed1_entries.iter().enumerate() {
            chrom_intervals
                .entry(entry.chrom.clone())
                .or_insert_with(Vec::new)
                .push(entry.to_interval(i));
        }

        for (chrom, intervals) in chrom_intervals {
            self.lappers.insert(chrom, Lapper::new(intervals));
        }
    }

    pub fn find_overlaps(&self, min_overlap_bp: Position) -> Vec<OverlapResult> {
        let mut overlaps = Vec::new();

        for entry2 in &self.bed2_entries {
            if let Some(lapper) = self.lappers.get(&entry2.chrom) {
                for interval in lapper.find(entry2.start, entry2.end) {
                    let entry1 = &self.bed1_entries[interval.val];

                    let overlap_start = entry1.start.max(entry2.start);
                    let overlap_end = entry1.end.min(entry2.end);
                    let overlap_length = overlap_end - overlap_start;

                    if overlap_length >= min_overlap_bp {
                        let overlap_fraction1 = overlap_length as f64 / entry1.length() as f64;
                        let overlap_fraction2 = overlap_length as f64 / entry2.length() as f64;

                        overlaps.push(OverlapResult {
                            entry1: entry1.clone(),
                            entry2: entry2.clone(),
                            overlap_length,
                            overlap_fraction1,
                            overlap_fraction2,
                        });
                    }
                }
            }
        }

        overlaps
    }

    pub fn write_overlaps(&self, overlaps: &[OverlapResult], output_path: &str) -> anyhow::Result<()> {
        use std::fs::File;
        use std::io::Write;

        let mut file = File::create(output_path)?;

        // Write header
        writeln!(file, "#chrom1\tstart1\tend1\textra1\tchrom2\tstart2\tend2\textra2\toverlap_length\toverlap_frac1\toverlap_frac2")?;

        for overlap in overlaps {
            writeln!(
                file,
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:.3}\t{:.3}",
                overlap.entry1.chrom,
                overlap.entry1.start,
                overlap.entry1.end,
                overlap.entry1.extra_fields.join("\t"),
                overlap.entry2.chrom,
                overlap.entry2.start,
                overlap.entry2.end,
                overlap.entry2.extra_fields.join("\t"),
                overlap.overlap_length,
                overlap.overlap_fraction1,
                overlap.overlap_fraction2,
            )?;
        }

        Ok(())
    }
}