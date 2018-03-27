import sys, re, pprint

f = open(sys.argv[1],'r')
fw = open('alunos.json','w')


sys.stdout = fw
alunos = re.compile('^A[0-9][0-9][0-9][0-9][0-9]')
ucs = re.compile('^H[0-9].*')


uc = 0
codigo = ''
dict_uc = {}
print '['
for line in f:
    if alunos.match(line):
        if uc != 0:
            print ']},'
        print '{\"%s\":' % line[:-2]
        uc = 0
    elif ucs.match(line):
        codigo = line[:-2]
        if uc == 0:
            print '[',
        else:
            print ',',
        print '\"%s\"' % (codigo),
        uc +=1
    elif codigo != '':
        value = line[:-2]
        if codigo not in dict_uc:
            dict_uc[codigo] = value
        codigo = ''
print ']}]'