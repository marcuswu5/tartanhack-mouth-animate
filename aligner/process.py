import mytextgrid
import csv
import subprocess
# Load the TextGrid file
subprocess.run(["mfa", "align", "data", "english_mfa", "english_mfa", "output"])
tg = mytextgrid.read_textgrid('output\harvard.TextGrid')

data = []

my_dict = {}

my_dict['e'] = 1
my_dict['æ'] = 1
my_dict['a'] = 1
my_dict['ɑ'] = 1

my_dict['i'] = 2
my_dict['ɪ'] = 2
my_dict['ɛ'] = 2
my_dict['j'] = 2
my_dict['ʎ'] = 2

my_dict['ɵ'] = 3
my_dict['o'] = 3
my_dict['ɔ'] = 3
my_dict['ɒ'] = 3

my_dict['y'] = 4
my_dict['ɨ'] = 4
my_dict['ʉ'] = 4
my_dict['ɯ'] = 4
my_dict['ʏ'] = 4
my_dict['ʊ'] = 4
my_dict['ø'] = 4
my_dict['ɘ'] = 4
my_dict['ɤ'] = 4
my_dict['ə'] = 4
my_dict['œ'] = 4
my_dict['ɜ'] = 4
my_dict['ɞ'] = 4
my_dict['ʌ'] = 4
my_dict['ɐ'] = 4
my_dict['ɶ'] = 4
my_dict['ɻ'] = 4
my_dict['k'] = 4
my_dict['x'] = 4
my_dict['χ'] = 4
my_dict['ħ'] = 4
my_dict['h'] = 4
my_dict['ɦ'] = 4
my_dict['ʔ'] = 4

my_dict['s'] = 5
my_dict['ɹ'] = 5
my_dict['ɴ'] = 5

my_dict['d'] = 6
my_dict['n'] = 6
my_dict['z'] = 6
my_dict['ʃ'] = 6
my_dict['ʒ'] = 6
my_dict['ʈ'] = 6
my_dict['ɖ'] = 6
my_dict['ɳ'] = 6
my_dict['ʂ'] = 6
my_dict['ʐ'] = 6
my_dict['ŋ'] = 6
my_dict['q'] = 6
my_dict['ɢ'] = 6

my_dict['ɸ'] = 7
my_dict['β'] = 7
my_dict['ⱱ'] = 7
my_dict['f'] = 7
my_dict['v'] = 7

my_dict['θ'] = 8
my_dict['ð'] = 8
my_dict['t'] = 8

my_dict['l'] = 9
my_dict['ɭ'] = 9
my_dict['ʟ'] = 9

my_dict['p'] = 10
my_dict['b'] = 10
my_dict['m'] = 10
my_dict['ɱ'] = 10

my_dict['u'] = 11
my_dict['ʋ'] = 11


for tier in tg:
    if tier.name == "words": continue

    if tier.is_interval():
        for interval in tier:
            if interval.text == "":
                data.append([str(interval.xmin), str(interval.xmax), 12])
            else:
                if interval.text[0] in my_dict:
                    data.append([str(interval.xmin), str(interval.xmax), my_dict[interval.text[0]]])
                else:
                    data[len(data) - 1][1] = str(interval.xmax)
                
with open('../csvfiles/output.csv', 'w', newline='') as csvfile:
    # Create a CSV writer object
    writer = csv.writer(csvfile)
    
    # Write all rows at once
    writer.writerows(data)