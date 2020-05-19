import re

# re_f = re.compile('\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')
re_f = re.compile('^[^/]')
f = re_f.search('a57a663a-9286-468d-9c0c-d2398f450eb6').group
print(f)