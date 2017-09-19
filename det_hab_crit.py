#!/usr/bin/env python3

from __future__ import print_function
import sys  # for sys.argv
import os   # for os.linesep 
from collections import OrderedDict

OUTPUT_NAME = "./new_output.txt"
TO_FEW_HABTRIALS = "to few habituation trials found, at least 6 are required."

class InvalidFile(Exception):
    '''
    Is raised when an file with unexpected content is found.
    '''
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return "file not understood: {}".format(self.reason)

class TrialData(object):
    def __init__(self, nthtrial, looking_time):
        self.nt, self.lt = nthtrial, looking_time


class ParseZepOutput(object):
    '''
    This class takes one input file and parses it.
    It is determined 1) which lines contain lines of the habituation phase.
    2) Which line contains the last line. 3) the output statistics are
    generated.
    '''
    HAB_IDENTIFIER = "HAB"
    '''This is the name of a column.'''
    TRIAL_COLUMN   = 5
    '''This is the column of the trial number.'''
    LOOKING_COLUMN = 9
    '''The column of the looking times.'''

    def __init__(self, filename):
        self.filename = filename

    def _filter_hab_lines(self, linelist):
        '''Generates a list of words that matches a habituation line'''
        for i in linelist:
            split = i.split()
            if len(split) != 11:
                continue
            if split[3] == ParseZepOutput.HAB_IDENTIFIER:
                yield split
        
    def _filter_last_trial_lines(self, hab_line_lists):
        '''Returns the last line of a trial.'''
        current_trial = 1
        l = list(hab_line_lists)
        if len(l) < 6: # at least 6 trials are required
            raise InvalidFile("Too few habituation trials found.")

        for i in range(len(l) - 1):
            trial_on_line = int(
                    l[i][ParseZepOutput.TRIAL_COLUMN]
                    )
            trial_on_next_line = int(
                    l[i+1][ParseZepOutput.TRIAL_COLUMN]
                    )
            if trial_on_next_line > trial_on_line: # It's the last
                yield l[i]
            
            if i + 1 == len(l) - 1: #yields the last entry in the list
                yield l[i + 1]
            

    def _generate_habituation_lines(self):
        '''Opens the file and returns the last line in the output of one trial
        '''
        habfile = open(self.filename)
        lines = habfile.readlines()
        filtered_lines = self._filter_hab_lines(lines)
        last_hab_entries = self._filter_last_trial_lines(filtered_lines)
        return last_hab_entries

    def trial_data(self):
        '''Returns a list of TrialData'''
        hablines = self._generate_habituation_lines()
        trials = []
        for i in hablines:
            ntrial          = int(i[ParseZepOutput.TRIAL_COLUMN])
            looking_time    = int(i[ParseZepOutput.LOOKING_COLUMN])
            trial           = TrialData(ntrial, looking_time)
            trials.append(trial)
        return trials

class DetermineHabituationStats(object):
    '''
    Determines the statistics for the habituation phase of a habituation
    experiment.
    '''

    def _avg(self, a_range):
        '''
        calculates the avarage of looking times over a range of
        self.statlist
        '''
        s = 0.0
        n = 0.0
        for i in a_range:
            s += self.statlist[i].lt
            n += 1.0
        return s/n

    def hab_crit(self):
        '''Determines the threshold for the habituation criterion.'''
        return self._avg(range(3)) * .65

    def determine_hab_crit(self):
        '''
        Determines the trial in which the infant met the habituation criterion.
        '''
        ntrial = -1
        self.avg_hab_met = -1
        for i in range(6, len(self.statlist)):
            if self._avg(range(i-3, i)) < self.crit:
                ntrial = i
                self.avg_hab_met = self._avg(range(i-3, i))
                break
        return ntrial

    def _sum_looking_times(self):
        '''Compute the looking times 
        '''
        s = 0.0
        self.lt_sum_habit = -1
        for i in range(len(self.statlist)):
            s += self.statlist[i].lt
            if i == self.hab_crit_met - 1:
                self.lt_sum_habit = s
        return s

    def last_three_trials(self):
        '''return a tuple with the last three looking times before the
           habituation criterion was met
        '''
        met = self.hab_crit_met
        l   = self.statlist
        return l[met - 3].lt, l[met - 2].lt, l[met - 1].lt

    def stats(self):
        stats = OrderedDict()
        stats["file"]       = self.filename
        stats["nhabtrials"] = str(len(self.statlist))
        stats["habituated"] = str(self.hab_crit_met)
        stats["avg 1-2-3"]  = str(self.avg_three)
        stats["lt sum hab"] = str(self.lt_sum_habit)
        stats["lt sum tot"] = str(self.lt_sum)
        stats["crit - 2"]   = str(self.third)
        stats["crit - 1"]   = str(self.second)
        stats["crit - 0"]   = str(self.last)
        stats["avg last3"]  = str((self.third + self.second + self.last)/3.0)
        stats["avg hab met"]= str(self.avg_hab_met)
        return stats
            
    def __init__(self, statlist, filename):
        if len(statlist) < 6:
            raise RunTimeError(TO_FEW_HABTRIALS)
        self.filename   = filename
        self.statlist   = statlist
        self.avg_three  = self._avg(range(3));
        self.crit       = self.hab_crit()
        self.hab_crit_met = self.determine_hab_crit()
        self.lt_sum     = self._sum_looking_times()
        self.third, self.second, self.last = self.last_three_trials()

if __name__ == "__main__":
    files = sys.argv[1:]
    f = open(OUTPUT_NAME, "w")
    outputstats = []
    output = ""
    for i in files:
        try:
            parser = ParseZepOutput(i)
            output_stats  = parser.trial_data();
            detstats = DetermineHabituationStats(output_stats, i)
            stats = detstats.stats()
            outputstats.append(stats)
        except InvalidFile as e:
            print("Unable to process {}, {}".format(i, str(e)), file=sys.stderr)
    
    if not outputstats:
        print("No valid inputs, nothing to do.")
        exit(0)

    #create header line 
    output = "\t".join(list(outputstats[0].keys()) + [os.linesep])
    for i in outputstats:
        row = "\t".join(list(i.values()))
        output = "".join([output, row, os.linesep])
    
    f.write(output)
    f.close()
