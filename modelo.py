import sys, json, pprint
from z3 import *

alunos_json  = json.load(open(sys.argv[1]))
horario_json = json.load(open(sys.argv[2]))


alunos = {}
slots = {}
presencas = {}
ucs = {}


# Carrega alunos e as ucs em que estao inscritos para o dicionario alunos {"A82382:[Hxxxxxx,Hxxxxx]"}
for elem in alunos_json:
    for al in elem:
        for uc in elem[al]:
            if al not in alunos:
                alunos[al] = [uc]
            else:
                alunos[al] += [uc]


n_dia = 0
n_hora = 8


#Carrega o horario e preenche os dicionarios slots e o ucs, slots --> {0:{9:[("HXXXX",TP1)]}}, ucs --> {Hxxxx:[(TP2,24)]}
for elem in horario_json: 
    if n_dia not in slots:
        slots[n_dia] = {}
    for dia in elem:
        for uc in elem[dia]:
            for codigo in uc:
                if codigo not in ucs:
                    ucs[codigo] = {}
                ucs[codigo][uc[codigo]['Turno']] = uc[codigo]['Capacidade']
                # if codigo not in ucs:
                #     ucs[codigo] = [(uc[codigo]['Turno'],uc[codigo]['Capacidade'])]
                # else:
                #     ucs[codigo] += [(uc[codigo]['Turno'],uc[codigo]['Capacidade'])]                    
                horaI = int(uc[codigo]['HoraI'][:2])
                horaF = int(uc[codigo]['HoraF'][:2])

                for hora in range(horaI,horaF):
                    if hora not in slots[n_dia]:
                        slots[n_dia][hora] = [(codigo,uc[codigo]['Turno'])]
                    else:
                        slots[n_dia][hora] += [(codigo,uc[codigo]['Turno'])]
    n_dia += 1


n_al = 0
n_uc = 0
n_turno = 0

for al in alunos:
    if al not in presencas:
        presencas[al] = {}
    for uc in alunos[al]:
        if uc in ucs:
            if uc not in presencas[al]:
                presencas[al][uc] = {}
            for turno in ucs[uc]:
                presencas[al][uc][turno] = Int('p_%s_%s_%s' % (al,uc,turno))

#pprint.pprint(presencas)


##################### RESTRICOES ######################################

#1 - Os valores possiveis sao 0 ou 1

values_c = [ Or(presencas[al][uc][turno] == 0, presencas[al][uc][turno] == 1) for al in presencas for uc in presencas[al] for turno in presencas[al][uc]]

#2 - Um aluno so pode ser atribuido a um e um so turno

um_turno_c =  [ Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) == 1 for al in presencas for uc in presencas[al]]

#3 - O numero de alocacoes para turno nao pode execeder a capacidade do mesmo
lista_capacidades = {}
for al in presencas:
    for uc in presencas[al]:
        if uc not in lista_capacidades:
            lista_capacidades[uc] = {}
        for turno in presencas[al][uc]:
            if turno not in lista_capacidades[uc]:
                lista_capacidades[uc][turno] = [ presencas[al][uc][turno] ]
            else:
                lista_capacidades[uc][turno] += [ presencas[al][uc][turno] ]
pprint.pprint(lista_capacidades)
capacidade_maxima_c = [ Sum(lista_capacidades[uc][turno]) <= ucs[uc][turno] for uc in lista_capacidades for turno in lista_capacidades[uc] ]


########################### SOLVER ############################
s = Solver()
s.add(values_c + um_turno_c + capacidade_maxima_c)

if s.check() == sat:
    m = s.model()
    r = {}
    for al in presencas:
        if al not in r:
            r[al] = {}
        for uc in presencas[al]:
            if uc not in r[al]:
                r[al][uc] = {} 
            for turno in presencas[al][uc]:
                #if turno == 1:
                r[al][uc][turno] = m.evaluate(presencas[al][uc][turno])
    pprint.pprint(r)
else:
    print "failed to solve"

# s.add(capacidade_maxima_c)
# if s.check() == sat:
#     m = s.model()
#     r = {}
#     for al in presencas:
#         if al not in r:
#             r[al] = {}
#         for uc in presencas[al]:
#             if uc not in r[al]:
#                 r[al][uc] = {} 
#             for turno in presencas[al][uc]:
#                 #if turno == 1:
#                 r[al][uc][turno] = m.evaluate(presencas[al][uc][turno])
#     pprint.pprint(r)
# else:
#     print "failed to solve"
