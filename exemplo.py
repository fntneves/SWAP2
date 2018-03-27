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
                    ucs[codigo] = [(uc[codigo]['Turno'],uc[codigo]['Capacidade'])]
                else:
                    ucs[codigo] += [(uc[codigo]['Turno'],uc[codigo]['Capacidade'])]                    
                horaI = int(uc[codigo]['HoraI'][:2])
                horaF = int(uc[codigo]['HoraF'][:2])

                for hora in range(horaI,horaF):
                    if hora not in slots[n_dia]:
                        slots[n_dia][hora] = [(codigo,uc[codigo]['Turno'])]
                    else:
                        slots[n_dia][hora] += [(codigo,uc[codigo]['Turno'])]
    n_dia += 1


for al in alunos:
    if al not in presencas:
        presencas[al] = {}
    for uc in alunos[al]:
        if uc in ucs:
            if uc not in presencas[al]:
                presencas[al][uc] = {}
            for tuplo in ucs[uc]:
                turno = tuplo[0]
                presencas[al][uc][turno] = Int('p')

# for dia in slots:
#     print dia
#     for hora in slots[dia]:
#         print hora,
#         print slots[dia][hora]       
        
            

