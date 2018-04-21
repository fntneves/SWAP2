# coding=utf-8
import sys, json, pprint, time
from z3 import *

alunos_json  = json.load(open(sys.argv[1]))
horario_json = json.load(open(sys.argv[2]))

#A[0-9][0-9][0-9][0-9][0-9]

alunos = {}
slots = {}
presencas = {}

# Carrega alunos e as ucs em que estao inscritos para o dicionario alunos {"A82382:[Hxxxxxx,Hxxxxx]"}
for al in alunos_json:
    if len(alunos) == int(sys.argv[3]):
        break
    if al in alunos:
        print 'Aluno %s repetido' % al
    for uc in alunos_json[al]:
        if al not in alunos:
            alunos[al] = [uc]
        else:
            alunos[al] += [uc]


n_dia = 0
minimo_hora = 100
maximo_hora = 0

#Carrega o horario e preenche os dicionarios slots, slots --> {Hxxxx:{TPX:[(Dia,Hora,Slots_1h,Capacidade)]}}}
for elem in horario_json: 
    for dia in elem:
        for uc in elem[dia]:
            for codigo in uc:
                horaI = int(uc[codigo]['HoraI'][:2])
                horaF = int(uc[codigo]['HoraF'][:2])
                minimo_hora = min(horaI,minimo_hora)
                maximo_hora = max(horaF,maximo_hora)
                # parte do codigo que adiciona o codigo-T para cadeiras com teoricas do aluno
                if len(codigo) > 6:
                    codigoAux = codigo[:6]
                    for al in alunos:
                        if codigoAux in alunos[al] and codigo not in alunos[al]:
                            alunos[al] += [codigo]
                if codigo not in slots:
                    slots[codigo] = {}
                turno = uc[codigo]['Turno']
                if turno not in slots[codigo]:
                    slots[codigo][turno] = [(n_dia,horaI,horaF-horaI,uc[codigo]['Capacidade'])]
                else:
                    slots[codigo][turno] += [(n_dia,horaI,horaF-horaI,uc[codigo]['Capacidade'])]
    n_dia += 1
maximo_dia = n_dia
# print('alunos:')
# pprint.pprint(alunos)
# print('ucs e slots:')
# pprint.pprint(slots)

n_al = 0
n_uc = 0
n_turno = 0

for al in alunos:
    if al not in presencas:
        presencas[al] = {}
    for uc in alunos[al]:
        if uc in slots:
            if uc not in presencas[al]:
                presencas[al][uc] = {}
            for turno in slots[uc]:
                presencas[al][uc][turno] = Int('p_%s_%s_%s' % (al,uc,turno))

##################### OBJECTIVOS ######################################

max_all = Sum([ presencas[al][uc][turno] for al in presencas for uc in presencas[al] for turno in presencas[al][uc] ])

##################### RESTRICOES ######################################

#- Os valores possiveis sao 0 ou 1

values_c = [ Or(presencas[al][uc][turno] == 0, presencas[al][uc][turno] == 1) for al in presencas for uc in presencas[al] for turno in presencas[al][uc]]


#- Um aluno so pode ser atribuido a um e um so turno se for TP

um_turnoTP_c =  [ Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) == 1 for al in presencas for uc in presencas[al] if len(uc) == 6]

#- Um aluno so pode ser atribuido a so turno se for T, nao sendo obrigatório

um_turnoT_c =  [ Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) <= 1 for al in presencas for uc in presencas[al] if len(uc) > 6]

#- O numero de alocacoes para turno nao pode execeder a capacidade do mesmo

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
capacidade_maxima_c = [ Sum(lista_capacidades[uc][turno]) <= slots[uc][turno][i][3] for uc in lista_capacidades for turno in lista_capacidades[uc] for i in range(len(slots[uc][turno]))]

# Aulas sem sobreposicoes
# Percorre todos os alunos e todas as ucs e junta todos os seus turnos num dicionario do tipo de acordo com o seu dia e hora, do tipo {Aluno:{Dia:{Hora:[Ucs]}}}
# Por ultimo, a soma dessa lista com as Ucs num determinado dia, numa determinada hora tem de ser no maximo 1, ou seja, tem de haver no maximo uma alocaçao

turnos = {}
for al in presencas:
    if al not in turnos:
        turnos[al] = {}
    for uc in presencas[al]:
        for t in presencas[al][uc]:
            for d in range(maximo_dia):
                if d not in turnos[al]:
                    turnos[al][d] = {}
                for h in range(minimo_hora,maximo_hora):
                    if h not in turnos[al][d]:
                        turnos[al][d][h] = []
                    tuplo = slots[uc][t]
                    for i in range(len(tuplo)):
                        if tuplo[i][0] == d and (tuplo[i][1] <= h < (tuplo[i][1] + tuplo[i][2])):
                            turnos[al][d][h] += [ presencas[al][uc][t] ]

sem_sobreposicoes_c = [ Sum(turnos[al][d][h]) <= 1 for al in turnos for d in turnos[al] for h in turnos[al][d] if len(turnos[al][d][h]) > 0 ]

########################### SOLVER ############################
print 'Numero de alunos: %s' % len(alunos)

s = Optimize()
s.maximize(max_all)

x = time.clock()
s.add(values_c)
print 'Solving constraint 0 or 1'
if s.check() != sat:
    print 'Failed to solver constraint 0 or 1'
    sys.exit()
x1 = time.clock()
print x1 - x

s.add(um_turnoT_c)
print 'Solving constraint tentar um turno T'
if s.check() != sat:
    print 'Failed to solver constraint tentar um turno t'
    sys.exit()
x = time.clock()
print x - x1

s.add(um_turnoTP_c)
print 'Solving constraint obrigatório um turno TP'
if s.check() != sat:
    print 'Failed to solver constraint obrigatório um turno TP'
    sys.exit()
x1 = time.clock()
print x1 - x

s.add(sem_sobreposicoes_c)
print 'Solving constraint sem sobreposicções'
if s.check() != sat:
    print 'Failed to solver constraint sem sobreposicções'
    sys.exit()
x = time.clock()
print x - x1

s.add(capacidade_maxima_c)
print 'Solving constraint capacidade maxima'
if s.check() != sat:
    print 'Failed to solver constraint capacidade maxima'
    sys.exit()
x1 = time.clock()
print x1-x

m = s.model()
r = {}
for al in presencas:
    if al not in r:
        r[al] = {}
    for uc in presencas[al]:
        if uc not in r[al]:
            r[al][uc] = {} 
        for turno in presencas[al][uc]:
            aloc = m.evaluate(presencas[al][uc][turno])
            if aloc == 1:
                r[al][uc][turno] = aloc

#alunos alocados a todas as cadeiras que estao inscritos
total_aloc = 0
n_tur = 0
nao_alocados = []
nao_alocados_t = []
alocacoes_finais = {}

for al in r:  
    for u in r[al]:
        if u not in alocacoes_finais:
            alocacoes_finais[u] = {}
        for t in r[al][u]:
            if r[al][u][t] == 1:
                n_tur += 1
                if t not in alocacoes_finais[u]:
                    alocacoes_finais[u][t] = 1
                else:
                    alocacoes_finais[u][t] += 1
    if n_tur >= len(r[al]) :
        total_aloc += 1
        n_tur = 0

#calcular alunos alocados a todas as cadeiras que estao inscritos  
for al in alunos:
    for uc in alunos[al]:
        if len(uc) == 6 and len(r[al][uc]) == 0 and al not in nao_alocados:
            nao_alocados.append(al)
        if len(uc) > 6 and len(r[al][uc]) == 0 and al not in nao_alocados_t:
            nao_alocados_t.append(al)


pprint.pprint(alocacoes_finais)
# pprint.pprint(r)
print 'Alunos alocados a todas as ucs: %s' % str(total_aloc)
print 'Alunos não alocados a praticas: '
pprint.pprint(nao_alocados)
print 'Alunos não alocados a teoricas: '
pprint.pprint(nao_alocados_t)
#print s.statistics()
# print s.sexpr()
