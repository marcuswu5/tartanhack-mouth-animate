import mytextgrid

# Load the TextGrid file
tg = mytextgrid.read_textgrid('output\harvard.TextGrid')

for tier in tg:
    print(f"Tier: {tier.name}")
    
    if tier.is_interval():
        for interval in tier:
            print(f"  [{interval.xmin} - {interval.xmax}] {interval.text}")
    else:
        # For PointTiers
        for point in tier:
            print(f"  Time: {point.time}, Mark: {point.text}")