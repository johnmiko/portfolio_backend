fname = 'lariel'

with open(fname + '.txt', 'r') as f:
    content = f.read()
old_content = content
with open(fname + '_new.txt', 'w+') as f:
    # content = re.sub("<.*\/.*>", "", content)
    content = content.replace("""These Pictures Was Taken Minutes Before The Beginning Of The Disaster!
FillyNews
See What the World's Most Beautiful Twins Are Up to Now!
FillyNews""", '')
    content = content.replace("""People from Calgary Are Using This to Get a Second Income!
Toptechnews
The $250 Bitcoin Investment That's Making People Rich
Toptechnews""", '')
    import re

    print(f'{len(content)}')
    content = re.sub(
        """These Pictures Was Taken Minutes Before The Beginning Of The Disaster!\nFillyNews\n.+\nFillyNews\n""", '',
        content)
    # print(content)
    print(f'{len(content)}')
    f.write(content)
