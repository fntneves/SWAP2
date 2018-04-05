import sys, json, pprint, time
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


#Carrega o horario e preenche os dicionarios slots e o ucs, slots --> {Hxxxx:{TPX:[(DIa,Hora,Slots_1h)]}}, ucs --> {Hxxxx:{TPx:Capacidade}}
for elem in horario_json: 
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
                if codigo not in slots:
                    slots[codigo] = {}
                for hora in range(horaI,horaF):
                    turno = uc[codigo]['Turno']
                    if turno not in slots[codigo]:
                        slots[codigo][turno] = (n_dia,horaI,horaF-horaI)
    n_dia += 1

#pprint.pprint(slots)

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
# PAULO

#capacidade_maxima_c = [ Sum([presencas[al][uc][turno] for al in presencas if uc in presencas[al]]) <= ucs[uc][turno] for uc in ucs  for turno in ucs[uc]]

# ZE
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
#pprint.pprint(lista_capacidades)
capacidade_maxima_c = [ Sum(lista_capacidades[uc][turno]) <= 57 for uc in lista_capacidades for turno in lista_capacidades[uc] ]
ucs[uc][turno]
#4 Aulas praticas sem sobreposicoes

########################### SOLVER ############################
s = Solver()
s.add(values_c)
x = time.clock()
print 'Solving constraint 1'
if s.check() != sat:
    print 'Failed to solver constraint 1'
    sys.exit()

x1 = time.clock()
print x1 - x

s.add(um_turno_c)

print 'Solving constraint 2'
if s.check() != sat:
    print 'Failed to solver constraint 2'
    sys.exit()
x = time.clock()

print x - x1
s.add(capacidade_maxima_c)

print 'Solving constraint 3'

if s.check() == sat:
    x1 = time.clock()
    print x1 - x
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
    alocacoes_finais = {}
    for al in r:
        for u in r[al]:
            if u not in alocacoes_finais:
                alocacoes_finais[u] = {}
            for t in r[al][u]:
                if r[al][u][t] == 1:
                    if t not in alocacoes_finais[u]:
                        alocacoes_finais[u][t] = 1
                    else:
                        alocacoes_finais[u][t] += 1
                
    pprint.pprint(alocacoes_finais)
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
