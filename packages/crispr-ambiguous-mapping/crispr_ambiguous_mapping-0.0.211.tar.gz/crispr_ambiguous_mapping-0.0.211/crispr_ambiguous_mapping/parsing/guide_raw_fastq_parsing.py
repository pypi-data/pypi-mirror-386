from typeguard import typechecked
from typing import Union
from typing import Callable
from typing import Counter as CounterType
from functools import partial
from collections import Counter

# DEPRECATED CLASS

'''
    Strategies to parse read
'''
@typechecked
def parse_read_positional(read_sequence: str, position_start: int, position_end: int) -> str:  
    return read_sequence[position_start:position_end]

@typechecked
def parse_read_left_flank(read_sequence: str, left_flank:str, guide_sequence_length:int) -> str: 
    position_start = read_sequence.find(left_flank) + len(left_flank)
    return read_sequence[position_start:position_start+guide_sequence_length]

@typechecked
def parse_read_right_flank(read_sequence: str, right_flank:str, guide_sequence_length:int) -> str:
    position_end = read_sequence.find(right_flank)
    return read_sequence[position_end-guide_sequence_length:position_end]


'''
    Extract the guide sequence from the read provided
'''
@typechecked
def parse_guide_sequence(read_sequence: str, parser_function: Callable) -> str:
    read_guide_sequence = parser_function(read_sequence)
    return read_guide_sequence




@typechecked
def get_raw_fastq_observed_sequence_counts(fastq_file: str, parse_left_flank: bool = True, parse_flank_sequence: Union[None, str] = None, cores: int=1) -> CounterType[str]:
    parse_guide_sequence_p = None
    if parse_left_flank:
        if parse_flank_sequence is None:
            print("No flank sequence passed. Setting left-flank default sequence to CACCG assuming U6 G+N20 guide")
            flank_sequence = "CACCG"
        else:
            flank_sequence = parse_flank_sequence

        parse_read_left_flank_p = partial(parse_read_left_flank, left_flank=flank_sequence, guide_sequence_length=20)
        parse_guide_sequence_p = partial(parse_guide_sequence, parser_function=parse_read_left_flank_p)
    else:
        if parse_flank_sequence is None:
            print("No flank sequence passed. Setting right-flank default sequence to GTTTT. If you are using sgRNA(F+E) design, flank sequence may need to be changed")
            flank_sequence = "GTTTT"
        else:
            flank_sequence = parse_flank_sequence
        
        parse_read_right_flank_p = partial(parse_read_right_flank, right_flank=flank_sequence, guide_sequence_length=20)
        parse_guide_sequence_p = partial(parse_guide_sequence, parser_function=parse_read_right_flank_p)

    # Looks for a flanking sequences (CACCG, or GTTTT) in the read, then extracts the 20nt guide sequence


    import gzip

    def parse_fastq_guide_sequences(file_handler):
        fastq_guide_sequences = []
        for line_number, line in enumerate(file):
            if line_number % 4 == 1:
                fastq_guide_sequences.append(parse_guide_sequence_p(line.strip()))
        
        # Count the unique observed sequences
        sequence_counter = Counter(fastq_guide_sequences)
        return sequence_counter
    
    if fastq_file.endswith('.gz'):
            print(f"Opening FASTQ.gz file with gzip, filename={fastq_file}")
            with gzip.open(fastq_file, "rt", encoding="utf-8") as file:
                return parse_fastq_guide_sequences(file)
    else:
        with open(fastq_file, "r") as file:
            return parse_fastq_guide_sequences(file)