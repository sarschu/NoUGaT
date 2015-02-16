#!/usr/bin/env python
# encoding: utf-8
"""
normalisation.py

Created by Bart Desmet on 2012-03-15.
Copyright (c) 2012 LT3. All rights reserved.
"""

import sys
import os
import codecs
import csv
import collections
import re
from itertools import islice


class SurplusError(Exception):
    def __init__(self, normalisation, surplus):
        self.norm = normalisation
        self.surplus = surplus
    
    
    def __str__(self):
        return "Error (l. {0}): surplus found while aligning: '{1}'".format(self.norm.rownumber, self.surplus.encode("utf-8"))
    


class MiscError(Exception):
    def __init__(self, normalisation):
        self.norm = normalisation
    
    
    def __str__(self):
        return "Error (l. {0}): some unhandled normalisation error: going from '{1}' over '{2}' to '{3}'".format(self.norm.rownumber, self.norm.tok_string.encode("utf-8"), self.norm.oper_string.encode("utf-8"), self.norm.norm_string.encode("utf-8"))
    


class NoPermMatchError(Exception):
    def __init__(self, normalisation, perms, input):
        self.norm = normalisation
        self.perms = perms
        self.input = input
    
    
    def __str__(self):
        return "Error (l. {0}): no permutations ('{1}') could be matched to '{2}' (to go from '{3}' to '{4}')".format(self.norm.rownumber, "', '".join(x.encode("utf-8") for x in self.perms), self.input.encode("utf-8"), self.norm.oper_string.encode("utf-8"), self.norm.norm_string.encode("utf-8"))
    


class TooManyPermMatchError(Exception):
    def __init__(self, normalisation, perms, matched_perms, input):
        self.norm = normalisation
        self.perms = perms
        self.matched_perms = matched_perms
        self.input = input
    
    
    def __str__(self):
        return "Error (l. {0}): too many permutations matched: '{1}' all matched with '{2}' (to go from '{3}' to '{4}')".format(self.norm.rownumber, "' and '".join(x.encode("utf-8") for x in self.matched_perms), self.input.encode("utf-8"), self.norm.oper_string.encode("utf-8"), self.norm.norm_string.encode("utf-8"))
    


class NoCommonSubstringError(Exception):
    def __init__(self, normalisation, string1, string2):
        self.norm = normalisation
        self.string1 = string1
        self.string2 = string2
    
    
    def __str__(self):
        print "Error (l. {0}): no common substring found between {1} and {2}".format(self.norm.rownumber, self.string1.encode("utf-8"), self.string2.encode("utf-8"))
    


class NoNextMatchError(Exception):
    def __init__(self, normalisation, sequence, inputstring):
        self.norm = normalisation
        self.sequence = sequence
        self.inputstring = inputstring
    
    
    def __str__(self):
        return "Error (l. {0}): could not align '{1}' to '{2}' because of this substring: '{3}' <-> ".format(self.norm.rownumber, self.norm.norm_string.encode("utf-8"), self.norm.oper_string.encode("utf-8"), self.inputstring.encode("utf-8")) + str(self.sequence)
    


class UnequalLengthSubstitutionError(Exception):
    def __init__(self, normalisation, sub_sequence, string):
        self.norm = normalisation
        self.sub_sequence = sub_sequence
        self.string = string
    
    
    def __str__(self):
        return "Warning (l. {0}): cannot yet align multiple substitutions of unequal length: '{1}' and '{2}' in '{3}' and '{4}'".format(self.norm.rownumber, "".join(x.text.encode("utf-8") for x in self.sub_sequence), self.string.encode("utf-8"), self.norm.oper_string.encode("utf-8"), self.norm.norm_string.encode("utf-8"))
    


class NoOperationsError(Exception):
    def __init__(self, normalisation):
        self.norm = normalisation
    
    
    def __str__(self):
        return "Error (l. {0}): operations column is empty, although '{1}' and '{2}' differ".format(self.norm.rownumber, self.norm.tok_string.encode("utf-8"), self.norm.norm_string.encode("utf-8"))
    


class DelTagError(Exception):
    def __init__(self, normalisation):
        self.norm = normalisation
    
    
    def __str__(self):
        return "Error (l. {0}): incorrect del tags: '{1}'".format( \
            self.norm.rownumber, self.norm.oper_string.encode("utf8"))
    


class TransTagError(Exception):
    def __init__(self, normalisation):
        self.norm = normalisation
    
    
    def __str__(self):
        return "Error (l. {0}): incorrect trans tags: '{1}'".format( \
            self.norm.rownumber, self.norm.oper_string)
    


class TokCorrespondenceError(Exception):
    def __init__(self, normalisation, simple):
        self.norm = normalisation
        self.simple = simple
    
    
    def __str__(self):
        return "Error (l. {0}): text in tokenisation column '{1}' differs from text in operations column '{2}'".format(self.norm.rownumber, self.norm.tok_string.encode("utf-8"), self.simple.encode("utf-8"))
    


class NormCorrespondenceError(Exception):
    def __init__(self, normalisation, oper_letter, norm_letter):
        self.norm = normalisation
        self.oper_letter = oper_letter
        self.norm_letter = norm_letter
    
    
    def __str__(self):
        return "Error (l. {0}): normalisation ('{1}') does not correspond with operations ('{2}')".format(self.norm.rownumber, self.norm.norm_string.encode("utf-8"), self.norm.oper_string.encode("utf-8"))
    


class Operation(object):
    """Represents an operation"""
    def __init__(self, op_type, text):
        assert op_type in ["normal", "insertion", "deletion", "transposition", "substitution"]
        self.type = op_type
        self.text = text
    
    
    def __repr__(self):
        try:
            if self.type == "deletion":
                return "{0}: {1}".format(self.type, self.text.encode("utf-8"))
            else:
                return "{0}: {1} => {2}".format(self.type, self.text.encode("utf-8"), self.alignment.encode("utf-8"))
        except AttributeError:
            return "{0}: {1}".format(self.type, self.text.encode("utf-8"))
    
    
    def add_alignment(self, text):
        self.alignment = text
    


def permute(word):
    return_list = []
    if len(word) == 1:
         # There is only one possible permutation
         return_list.append(word)
    else:
        # Return a list of all permutations using all characters
        for pos in range(len(word)):
            # Get the permutations of the rest of the word
            permute_list = permute(word[0:pos] + word[pos + 1:len(word)])
            # Now, tack the first char onto each word in the list
            # and add it to the output
            for item in permute_list:
                return_list.append(word[pos] + item)
    return list(set(return_list)) # make elements of return_list unique


def find_maximum_overlap(string1, string2):
    for l in range(len(string1), 0, -1):
        if string1[-l:] == string2[:l]:
            return string2[:l]
    raise NoCommonSubstringError(self, string1, string2)


class Normalisation(object):
    """Represents a series of operations"""
    def __init__(self):
        self.series = []
        self.rownumber = "?"
        self.normalised = False # By default, a Normalisation object is correct
                                # and thus has no operations column.
        self.aligned = False
        self.v = False # Verbose mode
    
    
    def add_rownumber(self, number):
        self.rownumber = number
    
    
    def add_input(self, anom_string, tok_string, oper_string, norm_string):
        self.anom_string = anom_string
        self.tok_string = tok_string
        self.fill_in_tok_string()
        self.oper_string = oper_string
        if self.oper_string:
            self.normalised = True
        self.norm_string = norm_string
    
    
    def validate_input(self):
        try: self.validate_no_operations()
        except NoOperationsError as e:
            return e
        if self.normalised: # These checks are only necessary on operations
            try: self.validate_del_tags()
            except DelTagError as e:
                return e
            try: self.validate_trans_tags()
            except TransTagError as e:
                return e
            try: self.validate_tok_oper_correspondence()
            except TokCorrespondenceError as e:
                return e
        return None
    
    
    def fill_in_tok_string(self):
        """Fill in the tokenized column if it is empty"""
        if self.tok_string == '':
            self.tok_string = self.anom_string
    
    
    def validate_no_operations(self):
        """Check if the operator column is empty. If so, the normalized column
        should be either empty or identical to the tokenized column.
        """
        if self.oper_string == '':
            if not self.norm_string:
                ### Empty norm_string = no operations required
                ### Set norm_string to be identical to tok_string
                self.norm_string = self.tok_string
                return
            if self.tok_string != self.norm_string:
                if self.tok_string.lower() != self.norm_string.lower():
                    if "".join(re.split(r'\[.*?\]', self.tok_string.lower())) != self.norm_string.lower():
                        ### The second if-clause is hardly ever performed
                        ### (which is why it is in a separate if-clause)
                        ### Normalisations do not take into account
                        ### capitalization, so we can ignore it
                        raise NoOperationsError(self)
    
    
    def validate_del_tags(self):
        """Check if the number of opening del tags matches the number
        of closing del tags.
        """
        if len(re.findall(r'<del>', self.oper_string)) != len(re.findall(r'</del>', self.oper_string)):
            raise DelTagError(self)
    
    
    def validate_trans_tags(self):
        """Check if the number of opening trans tags matches the number
        of closing trans tags.
        """
        if len(re.findall(r'<trans>', self.oper_string)) != len(re.findall(r'</trans>', self.oper_string)):
            raise TransTagError(self)
    
    
    def validate_tok_oper_correspondence(self):
        """Check if the text in the tokenized column is identical
        to the text in the operations column, without all the operators.
        """
        # Remove all instances of <del>, </del>, <trans>, </trans>, § and #
        simple = self.oper_string.split("<del>")
        simple = "".join(simple)
        simple = simple.split("</del>")
        simple = "".join(simple)
        simple = simple.split("<trans>")
        simple = "".join(simple)
        simple = simple.split("</trans>")
        simple = "".join(simple)
        simple = simple.split(u"§")
        simple = "".join(simple)
        simple = simple.split("#")
        simple = "".join(simple)
        # The string in simple should now only contain the original characters
        try: assert simple == self.tok_string
        except AssertionError:
            # For now, we allow additional whitespace in the operations column
            simple = simple.split(" ")
            simple = "".join(simple)
            if simple != "".join(self.tok_string.split(" ")):
                # Capitalization can be ignored
                if simple.lower() != "".join(self.tok_string.split(" ")).lower():
                    # If this still fails, we have an error.
                    raise TokCorrespondenceError(self, simple)
    
    
    def __repr__(self):
        return "Success (l. {0}): {1} is aligned to {2} as follows: {3}".format(            self.rownumber, self.oper_string.encode("utf-8"), self.norm_string.encode("utf-8"), ", ".join([str(x) for x in self.series]))
    
    
    def parse_operations(self):
        """Parses self.oper_string (a string with operations in it),
        to construct a series of Operation objects.
        """
        # Compile regular expression first
        re_del = re.compile(r'<del>(.+?)</del>')
        re_trans = re.compile(r'<trans>(.+?)</trans>')
        re_sub = re.compile(ur'§(.+?)§')
        
        # Loop over string until all characters have been matched
        inputstring = self.oper_string
        self.series = []
        while inputstring:
            if re_del.match(inputstring):
                m = re_del.match(inputstring)
                assert m.group(1)
                self.series.append(Operation("deletion", m.group(1)))
                inputstring = inputstring[m.end():]
            elif re_trans.match(inputstring):
                m = re_trans.match(inputstring)
                assert m.group(1)
                self.series.append(Operation("transposition", m.group(1)))
                inputstring = inputstring[m.end():]
            elif re_sub.match(inputstring):
                m = re_sub.match(inputstring)
                assert m.group(1)
                self.series.append(Operation("substitution", m.group(1)))
                inputstring = inputstring[m.end():]
            elif inputstring[0] == "#":
                self.series.append(Operation("insertion", "#"))
                inputstring = inputstring[1:]
            else:
                self.series.append(Operation("normal", inputstring[0]))
                inputstring = inputstring[1:]
    
    
    def align_entire_string(self):
        """Tries to align oper_string to norm_string, returns errors."""
        assert self.normalised
        inputstring = self.norm_string[:]
        try:
            self.series, surplus = self.align(self.series, inputstring)
            if surplus:
                return SurplusError(self, surplus)
            self.aligned = True
        except NormCorrespondenceError as e:
            return e
        except SurplusError as e:
            return e
        except UnequalLengthSubstitutionError as e:
            return e
        except NoCommonSubstringError as e:
            return e
        except NoNextMatchError as e:
            return e
        except NoPermMatchError as e:
            return e
        except TooManyPermMatchError as e:
            return e
        except MiscError as e:
            return e
        except:
            print "Some unknown error occurred: The normalized string '{0}' could not be aligned to the operations '{1}'".format(self.norm_string, self.oper_string)
            
    
    
    def align_sub_sequence(self, sub_sequence, string):
        if len(sub_sequence) == len(string):
            for index in range(len(sub_sequence)):
                sub_sequence[index].add_alignment(string[index])
            return sub_sequence
        else:
            ### Try replacing "ij" occurrences with "y"
            new_string = string.replace("ij", "y")
            if len(sub_sequence) == len(new_string):
                for index in range(len(sub_sequence)):
                    sub_sequence[index].add_alignment(new_string[index].replace("y", "ij"))
                return sub_sequence
            elif len(sub_sequence) == 1:
                ### There is only one substitution, so all characters can be aligned
                sub_sequence[0].add_alignment(string)
                return sub_sequence
            else:
                ### There is no code to align multiple substitutions of unequal length
                raise UnequalLengthSubstitutionError(self, sub_sequence, string)
    
    
    def align(self, series, inputstring, direction = "right", full_inputstring = False):
        """Aligns inputstring (a normalized string) to an operation series.
        Returns the series, enriched with alignments.
        direction: parsing is done as requested (right = from left to right)
        full_inputstring: necessary to return left_surplus on substrings
        """
        return_series = []
        surplus = None
        ### If the series is empty (which will be the case when doing a
        ### recursive self.align on a string split on a pattern occurring at
        ### the beginning or end, e.g. §ab§cd will be split on ab, and parsed
        ### again with self.align on '' and 'cd'. In the first case, an empty
        ### series should be returned, and the full string as surplus.
        if not len(series):
            return [], inputstring
        
        ### Zeroeth, align all 1-1 correspondences at the beginning and end
        
        ### First, check for remaining transpositions (n-n)
        transpos = [x for x in series if x.type == "transposition"]
        subs = [x for x in series if x.type == "substitution"]
        if transpos:
            # print "There are transpositions!"
            next_transpo = transpos[0]
            permutations = permute(next_transpo.text)
            matched_permutations = [p for p in permutations if p in inputstring]
            if len(matched_permutations) < 1:
                raise NoPermMatchError(self, permutations, inputstring)
            elif len(matched_permutations) > 1:
                raise TooManyPermMatchError(self, permutations, matched_permutations, inputstring)
            matches = re.findall(matched_permutations[0], inputstring)
            try: assert len(matches) == 1
            except AssertionError:
                
                print matched_permutations, matches, inputstring
                raise
            match = matches[0]
            substrings = inputstring.split(match, 1)
            next_transpo.add_alignment(match)
            preceding_series, right_surplus = self.align(series[:series.index(next_transpo)], substrings[0])
            if right_surplus:
                raise SurplusError(self, right_surplus)
            following_series, left_surplus  = self.align(series[series.index(next_transpo) + 1:], substrings[1])
            if left_surplus:
                raise SurplusError(self, left_surplus)
            return_series = preceding_series + [next_transpo] + following_series
            return return_series, surplus
        
        ### Second, check for remaining substitutions (n-m)
        elif subs:
            # print "There are substitutions!"
            # We look for a series of contiguous subs (usually just 1)
            preceding_sequence = series[:series.index(subs[0])]
            next_sub_sequence = [subs.pop(0)]
            while series[series.index(next_sub_sequence[-1])+1:]:
                next_element = series[series.index(next_sub_sequence[-1])+1:][0]
                if next_element.type == "substitution":
                    next_sub_sequence.append(next_element)
                else:
                    break
            following_sequence = series[series.index(next_sub_sequence[-1])+1:]
            
            if self.v: print "\nBefore starting", preceding_sequence, next_sub_sequence, following_sequence, inputstring
            
            ## Align preceding sequence
            if preceding_sequence:
                preceding_sequence, right_surplus = self.align(preceding_sequence, inputstring) ### Should match at the beginning of inputstring
                if self.v: print "After preceding", preceding_sequence, next_sub_sequence, following_sequence, right_surplus
            else:
                if self.v: print "No preceding sequence! Saving right_surplus as", inputstring
                right_surplus = inputstring
            
            ## Align following sequence
            v_next = False
            if following_sequence:
                no_del_len = len([x for x in following_sequence if x.type != "deletion"])
                if no_del_len == 0: ### If there are only deletions, all
                    ### remaining characters should go to the substitution
                    ### Just align the deletions with nothing and return all
                    ### remaining characters as surplus for the substitution
                    following_sequence, left_surplus = self.align(following_sequence, "")
                    left_surplus = right_surplus
                else:
                    next_match_index = None
                    if v_next: print "Looking for next_match_index"
                    for index in range(1, len(right_surplus)):
                        if v_next: print "Index:", index
                        try:
                            if v_next: print following_sequence[0], right_surplus[index]
                            self.align([following_sequence[0]], right_surplus[index])
                            next_match_index = index
                            break
                        except:
                            continue
                    if not next_match_index:
                        raise NoNextMatchError(self, following_sequence, right_surplus)
                    if v_next: print "Found it:", next_match_index
                    if v_next: print "Before following", preceding_sequence, next_sub_sequence, following_sequence, right_surplus[next_match_index:], inputstring
                    following_sequence, left_surplus = self.align(following_sequence, right_surplus[next_match_index:], direction = "left", full_inputstring = inputstring) ### inputstring will contain some characters (at the beginning) which belong to the substitution
                    if self.v: print "After following", preceding_sequence, next_sub_sequence, following_sequence, left_surplus
            else:
                if self.v: print "No following sequence! Saving left_surplus as", inputstring
                left_surplus = inputstring
            
            ## Find overlap between surpluses
            if self.v: print "Trying to find overlap between", left_surplus, "and", right_surplus
            overlap = find_maximum_overlap(left_surplus, right_surplus)
            if self.v: print "Overlap", overlap
            
            ## Align overlap to sub_sequence
            sub_sequence = self.align_sub_sequence(next_sub_sequence, overlap)
            
            ## Return
            return_series = preceding_sequence + sub_sequence + following_sequence
            if surplus == None and full_inputstring and inputstring != full_inputstring:
                start_index = full_inputstring.find(inputstring)
                surplus = full_inputstring[:start_index]
            if self.v: print return_series, surplus, "\n"
            return return_series, surplus
        
        ### Now, the series only contains normal, deletion and
        ### insertion (1-1) operations. We parse in the intended direction
        else:
            # print "There are only 1-on-1 relations left!"
            pop_index = {"right": 0, "left": -1}[direction]
            inputlist = list(inputstring) # Recast inputstring as a list
            return_series = []
            while series:
                element = series.pop(pop_index)
                # print element
                op_type = element.type
                text = element.text
                if op_type == "deletion":
                    element.add_alignment("")
                    return_series.append(element)
                    continue # Go to the next element in the series
                ### If there is a normal letter, or insertion, one character
                ### should be popped from the inputlist
                try:
                    next_letter = inputlist.pop(pop_index)
                except IndexError:
                    raise MiscError(self)
                if op_type == "normal":
                    ### For normal characters, we do an extra equality check
                    ### We can't do this for insertion
                    if text.lower() != next_letter.lower():
                        raise NormCorrespondenceError(self, text, next_letter)
                element.add_alignment(next_letter)
                return_series.append(element)
                # print return_series
            no_del_len = len([x for x in return_series if x.type != "deletion"])
            if full_inputstring:
                inputstring = full_inputstring
            surplus = {"right": inputstring[no_del_len:],
                       "left": inputstring[:-no_del_len]}[direction]
            if direction == "left":
                return_series.reverse()
            return return_series, surplus
    


def csv_to_inputrows(inpath, encoding, google_doc = False, delimiter = ",", header = False, remove_whitespace = True, no_skipped = False):
    """Reads input from an Excel CSV file and stores it in inputrows,
    a list of rows (also lists), containing the cell values as Unicode strings.
    Optionally, leading and trailing whitespace is removed from these values.
    Optionally, Google Doc peculiarities are cleaned in the input.
    Optionally, skip messages that have not been normalized.
    """
    ### The csv module is not Unicode-enabled. This is why we read in as is, and
    ### decode the buffer later (outside csv) with the intended encoding.
    csv_input = csv.reader(open(inpath, "rU"), dialect="excel", delimiter = delimiter)
    inputrows = []
    for row in csv_input:
        inputrows.append([unicode(x.decode(encoding)).replace(u"\u200e","").replace(u"\xa0"," ") for x in row])
    if remove_whitespace:
        inputrows = [[x.strip().replace("  "," ") for x in row] for row in inputrows]
    if google_doc:
        plus_re  = re.compile(r"^'\+")
        equal_re = re.compile(r"^'=")
        apos_re  = re.compile(r"^''")
        zero_re  = re.compile(r"^'0")
        inputrows = [[re.sub(plus_re, "+", re.sub(equal_re, "=", re.sub(apos_re, "'", re.sub(zero_re, "0", x)))) for x in row] for row in inputrows]
    if header:
        inputrows = inputrows[1:]
    if no_skipped:
        skip = False
        purged_inputrows = []
        for row in inputrows:
            try: assert len(row) >= 4
            except AssertionError:
                print row
                raise
            if row[2]: # New post
                if row[0]:
                    skip = True # Skipped post
                else: skip = False
            if not skip:
                purged_inputrows.append(row)
        return purged_inputrows
    return inputrows


def outputrows_to_csv(outpath, encoding, outputrows):
    csv_output = csv.writer(open(outpath, "wb"), dialect="excel", delimiter=";")
    for row in outputrows:
        csv_output.writerow([x.encode(encoding) for x in row])


def complete_inputrows(inputrows):
    """If the second column (tokenisations) is empty, we store the
    same value there as in the first columns (anomalous).
    """
    for row in inputrows:
        if row[1] == '':
            row[1] = row[0]
    return inputrows


def get_linedict_from_csv(inpath, encoding, delimiter = ",", offset = 3, google_doc = False, no_skipped = True, header = False):
    ### Read CSV file
    inputrows = csv_to_inputrows(inpath, encoding, google_doc = google_doc, header = header, delimiter = delimiter, no_skipped = no_skipped)
    
    ### Check if all rows have 4 elements
    assert all(check_row(x, offset) for x in inputrows)
    
    ### Loop over all lines, collect input and output sentences
    linedict = {}
    ne_count=0
    post = 0
    for row in inputrows:
        if row[2]:
            count=0
            post += 1
            k = unicode(row[2])
            linedict[k]={"ori": [],"tok":[], "tgt": [],"ne":[]}
        if row[3]: # Ignore empty lines
            linedict[k]["ori"].append(row[3])
            if len(row)>21:
                if row[21] not in ["O",""]: 
                    linedict[k]["ne"].append(count)
                    ne_count+=1
            else:
                if row[10]: 
                    linedict[k]["ne"].append(count)
                    ne_count+=1

            if row[7]:
                    linedict[k]["tok"].append(u"•")
                    linedict[k]["tgt"].append(u"•")
            elif row[8]:
                linedict[k]["tok"].append(u"•")
                linedict[k]["tgt"].append(u"•")
            elif row[9]:
                linedict[k]["tgt"].append(u"•")
                linedict[k]["tok"].append(u"•")
            
            elif row[6] or row[4]:
                if row[6]:
                    linedict[k]["tgt"].append(row[6])
                else:
                    linedict[k]["tgt"].append(row[3])
                if row[4]:
                    linedict[k]["tok"].append(row[4])
                else:
                    linedict[k]["tok"].append(row[3])
            else:
                linedict[k]["tgt"].append(row[3])
                linedict[k]["tok"].append(row[3])
                    
            count+=1

    print ne_count
    return linedict


def print_files_from_linedict(linedict, outdir, threshold = None, overlap = 0):
    extensions = ["ori", "tok", "tgt"]
    if not threshold: # Lines have no size limit
        for ext in extensions:
            f = codecs.open(os.path.join(outdir, "output" + "." + ext), "w", "utf8")
            for k in sorted(linedict.keys()):
                f.write(" ".join(linedict[k][ext]) + "\n")
            f.close()
        return
    
    # Lines do have a limit
    new_linedict = {}
    import operator
    
    def is_short_enough(threshold, start, end = None):
        """Checks for all extensions whether the words from start to end index
        form a string that is shorter than threshold"""
        for ext in extensions:
            if (sum(len_dict[ext][start:end]) + len(len_dict[ext][start:end]) - 1) >= threshold:
                return False
        return True
    



def check_row(row, offset):
    # print row
    if len(row[offset:offset+4]) != 4:
        return False
    else: return True


def read_csv_for_flag_checks(inpath, encoding, delimiter = ";", offset = 0, google_doc = True, no_skipped = False):
    ### Read CSV file
    inputrows = csv_to_inputrows(inpath, encoding, delimiter = delimiter, google_doc = google_doc, header = True, no_skipped = no_skipped)
    
    ### Check if all rows have 4 elements
    assert all(check_row(x, offset) for x in inputrows)
    
    inputrows = [x[offset:] for x in inputrows]
    
    def special_char_column(index, flag_column, norm):
        for char in [u"•", u"±", u"∞", u"™"]:
            if char in flag_column:
                for s in flag_column.split(char):
                    if not s in norm:
                        print "Warning (l. %d): error in special character column: %s <-> %s" % (index+1, flag_column, norm)
                return True
        return False
    
    for index, row in enumerate(inputrows):
        if not row[0]:
            if any(x for x in row):
                print "Warning (l. %d): flag in empty line (message separator)" % (index+1)
        norm = row[3]
        if not norm: norm = row[1]
        if not norm: norm = row[0]
        for flag_column in row[4:]:
            if flag_column:
                if special_char_column(index, flag_column, norm):
                    continue
                elif flag_column == "x":
                    continue
                else:
                    flag_indices = flag_column.split(",")
                    try: flag_indices = [int(x) for x in flag_indices]
                    except:
                        print "Warning (l. %d): unexpected flag: %s" % (index+1, flag_column)
                    for flag_index in flag_indices:
                        if not (0 < flag_index <= len(norm.split(" "))):
                            print "Warning (l. %d): incorrect 1-based flag index: %s <-> %s" % (index+1, flag_column, norm)


def read_csv_for_validation(inpath, encoding, delimiter = ";", offset = 0, google_doc = True, no_skipped = False):
    """Reads a CSV file containing four columns, starting from index offset:
    - Anomalous
    - Tokenized
    - Operations
    - Normalized
    Outputs a list of tuples with this information.
    If the input CSV was made originally in Google Doc, some peculiarities have
    to be removed.
    """
    ### Read CSV file
    inputrows = csv_to_inputrows(inpath, encoding, delimiter = delimiter, google_doc = google_doc, header = True, no_skipped = no_skipped)
        
    ### Check if all rows have 4 elements
    assert all(check_row(x, offset) for x in inputrows)
    
    ### Initialize errordict
    errordict = {"missing operations": 0,
                 "incorrect del tag": 0,
                 "incorrect trans tag": 0,
                 "incorrect operation": 0,
                 "incorrect normalisation": 0,
                 }
    
    ### Now we loop over all the rows, checking a number of things for every row
    ### We also store all normalisations in a list
    normalisations = []
    for index, row in enumerate(inputrows):
        n = Normalisation()
        n.v = False # Set verbosity
        n.add_input(row[offset], row[offset+1], row[offset+2], row[offset+3])
        n.add_rownumber(index + 1)
        error = n.validate_input()
        if error:
            print error
            continue # Stop parsing and move to next input row
        
        if n.normalised:
            n.parse_operations()
            error = n.align_entire_string()
            if error:
                # print type(error)
                print error
                if isinstance(error, UnequalLengthSubstitutionError):
                    ### These are not really errors, so they get added
                    normalisations.append(n)
                    pass
                continue # Stop parsing and move to next input row
            normalisations.append(n)
            print_successes = False
            if print_successes:
                print n
    
    ### Return the normalisations
    return normalisations


def calculate_len_dict_avg(len_dict):
    sum_dotproduct = sum(x*len(y) for x, y in len_dict.iteritems())
    sum_values = sum(len(x) for x in len_dict.itervalues())
    avg = sum_dotproduct/float(sum_values)
    return avg


def analyze_string_len_diffs(normalisations):
    orig_len_dict = {}
    norm_len_dict = {}
    diff_len_dict = {}
    for n in normalisations:
        origl = len(n.tok_string)
        norml = len(n.norm_string)
        orig_len_dict[origl] = orig_len_dict.get(origl, []) + [n]
        norm_len_dict[norml] = norm_len_dict.get(norml, []) + [n]
        diff = norml - origl
        diff_len_dict[diff] = diff_len_dict.get(diff, []) + [n]
    print "Original (tokenized) string lengths: (average: {})".format(calculate_len_dict_avg(orig_len_dict))
    print "(3 15 would mean there are 15 occurrences of a tokenized string of 3 characters long)"
    for length in sorted(orig_len_dict.keys()):
        print length, len(orig_len_dict[length])
    print "\nNormalized string lengths: (average: {})".format(calculate_len_dict_avg(norm_len_dict))
    print "(3 15 would mean there are 15 occurrences of a normalized string of 3 characters long)"
    for length in sorted(norm_len_dict.keys()):
        print length, len(norm_len_dict[length])
    print "\nString length differences: (average: {})".format(calculate_len_dict_avg(diff_len_dict))
    print "(-2 4 would mean that there are 4 occurrences where the normalized string is 2 characters shorter than the tokenized string)"
    for diff in sorted(diff_len_dict.keys()):
        print diff, len(diff_len_dict[diff])#, [x.series for x in diff_len_dict[diff][:3]]


def analyze_normalisations(normalisations):
    operations = [x for norm in normalisations for x in norm.series]
    oper_dict = {}
    for oper in operations:
        try: oper_dict[oper.type].append(oper)
        except KeyError:
            oper_dict[oper.type] = [oper]
    print "Found {0} normalised strings with {1} operations".format(len(normalisations), len(operations))
    for key in oper_dict:
        print key, len(oper_dict[key])#, oper_dict[key]
    return oper_dict


def write_operations_to_csv(normalisations, filepath, encoding):
    ### Read CSV file
    outputrows = []
    for n in normalisations:
        for o in n.series:
            if o.type == "normal": continue
            try: 
                outputrows.append([o.type, o.text, o.alignment, n.oper_string, n.norm_string, str(n.rownumber)])
            except AttributeError:
                outputrows.append([o.type, o.text, "???", n.oper_string, n.norm_string, str(n.rownumber)])
    outputrows_to_csv(filepath, encoding, outputrows)


def make_anomalous_input_from_csv():
    """Converts a CSV list with the input SMS (one per line) to a CSV
    with the original SMS in the first column, and all the tokens (split
    on spaces) in the second column, one token per line."""
    dir_name = os.path.dirname(os.path.realpath(__file__))
    input_csv = os.path.join(dir_name, "sms.csv")
    output_csv = os.path.join(dir_name, "sms_out_2.csv")
    input = csv.reader(open(input_csv, "rU"), dialect="excel", delimiter = ";")
    output = csv.writer(open(output_csv, "wb"), dialect="excel", delimiter = ";")
    for row in input:
        counter = 1
        if "wkker" in row[1]:
            print row[1]
            print type(row[1])
        text = row[1].replace('\xc2\xa0', ' ')
        for token in text.split():
            if counter == 1:
                output.writerow([row[0], text, token])
            else:
                output.writerow([None, None, token])
            counter += 1
        output.writerow([None])

def make_anomalous_input_from_txt(input_path, output_path, id_prefix, input_encoding = "utf8"): 
    """Converts a TXT file with the input SMS (one per line) to a CSV
    with the original SMS in the first column, and all the tokens (split
    on spaces) in the second column, one token per line."""
    ### WERKT NOG NIET!
    assert os.path.isfile(input_path)
    assert os.path.isdir(os.path.dirname(output_path))
    assert not os.path.isfile(output_path)
    input = codecs.open(input_path, "r", input_encoding)
    output = csv.writer(open(output_path, "wb"), dialect="excel", delimiter = ";")
    id_counter = 0
    for text in input:
        text = text.strip()
        id_counter += 1
        text_id = "%s%05d" % (id_prefix, id_counter)
        counter = 1
        for token in text.split():
            if counter == 1:
                output.writerow([text_id, text, token])
            else:
                output.writerow([None, None, token])
            counter += 1
        output.writerow([None])


def main():
    ### Parameters:
    ## - inpath = waar het normalisatiecorpus staat (in csv)
    inpath = "/home/sarah/Dropbox/Normalisatie/Datasets/CSV_GoogleDocs/Dutch_without_NE/sms/sms_dev_1"
    # inpath = "/home/sarah/Desktop/copiletestwithoutspec/sns_test"
    ## - de encoding van het normalisatiecorpus. Verander dit als het programma
    ##   stopt met een UnicodeDecodeError (bv naar utf-8, latin1 of mac_roman)
    encoding = "utf8"
    ## - waar het overzicht van de normalisaties opgeslaan moet worden
    # csv_outpath = "/Users/orphee/Dropbox/Normalisatie/IAA/LIEN.csv/sns_operations90.csv"
    ## - in welke encoding dat overzicht moet. Verander dit als het bestand er 
    ##   in Excel niet juist uitziet (bv §-teken is verkeerd). 
    # output_encoding = "utf8"
    
    ## Bepaal hoeveel kolommen er voor de Anomalouskolom komen
    offset = 3
    no_skipped = False
    
    print "\nREADING AND ALIGNING NORMALISATIONS\n"
    # normalisations = read_csv_for_validation(inpath, encoding, delimiter=",", offset=offset, google_doc = False, no_skipped = no_skipped)
    # read_csv_for_flag_checks(inpath, encoding, delimiter=",", offset=offset, google_doc = True, no_skipped = no_skipped)
    
    linedict = get_linedict_from_csv(inpath, encoding, offset=offset, no_skipped=no_skipped)
    print linedict
    outdir = "/home/sarah/Dropbox/Normalisatie/Datasets/CSV_GoogleDocs/Dutch_without_NE/sms/"
    threshold = 90000
    print_files_from_linedict(linedict, outdir, threshold, overlap = 1)
    
    # print "\nNORMALISATION COUNTS:\n"
    #     oper_dict = analyze_normalisations(normalisations)
    #     write_operations_to_csv(normalisations, csv_outpath, output_encoding)
    #     
    #     print "\nSTRING LENGTH COUNTS:\n"
    #     analyze_string_len_diffs(normalisations)
    

if __name__ == '__main__':
    main()

