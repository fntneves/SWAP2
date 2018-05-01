# coding=utf-8
import sys, json, pprint, time
from z3 import *

alunos_json  = json.load(open(sys.argv[1]))
horario_json = json.load(open(sys.argv[2]))
grupos_json = json.load(open('grupos.json'))

suf_teoria = '-T'

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

dias_slots = {}

#Carrega o horario e preenche os dicionarios slots, slots --> {Hxxxx:{TPX:[(Dia,Hora,Slots_1h,Capacidade)]}}}
for elem in horario_json:
    maximo_slot = 0
    for dia in elem:
        for uc in elem[dia]:
            for codigo in uc:
                horaI = uc[codigo]['HoraI']
                horaF = uc[codigo]['HoraF']
                maximo_slot = max(horaF,maximo_slot)
                # parte do codigo que adiciona o codigo-T para cadeiras com teoricas do aluno
                if codigo[-2:] == suf_teoria:
                    codigoAux = codigo[:6]
                    for al in alunos:
                        if codigoAux in alunos[al] and codigo not in alunos[al]:
                            alunos[al] += [codigo]
                if codigo[:6] == 'ALMOCO':
                    for al in alunos:
                        if codigo not in alunos[al]:
                            alunos[al] += [codigo]                        
                if codigo not in slots:
                    slots[codigo] = {}
                turno = uc[codigo]['Turno']
                if turno not in slots[codigo]:
                    slots[codigo][turno] = [(n_dia,horaI,horaF,uc[codigo]['Capacidade'])]
                else:
                    slots[codigo][turno] += [(n_dia,horaI,horaF,uc[codigo]['Capacidade'])]
        if n_dia not in dias_slots:
            dias_slots[n_dia] = maximo_slot
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

max_Teoricas = Sum([ presencas[al][uc][turno] for al in presencas for uc in presencas[al] for turno in presencas[al][uc] if uc[-2:] == suf_teoria ])

##################### RESTRICOES ######################################

#- Os valores possiveis sao 0 ou 1

values_c = [ Or(presencas[al][uc][turno] == 0, presencas[al][uc][turno] == 1) for al in presencas for uc in presencas[al] for turno in presencas[al][uc]]


#- Um aluno so pode ser atribuido a um e um so turno se for TP

um_turnoTP_c =  [ Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) == 1 for al in presencas for uc in presencas[al] if not (uc[-2:] == suf_teoria) ]

#- Um aluno so pode ser atribuido a so turno se for T, nao sendo obrigatório

um_turnoT_c =  [ Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) <= 1 for al in presencas for uc in presencas[al] if uc[-2:] == suf_teoria]

#- O numero de alocacoes para turno nao pode execeder a capacidade do mesmo

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

capacidade_maxima_TP_c = [ Sum(lista_capacidades[uc][turno]) <= slots[uc][turno][i][3] for uc in lista_capacidades for turno in lista_capacidades[uc] for i in range(len(slots[uc][turno])) if uc[-2:] != suf_teoria ]

capacidade_maxima_T_c = [ Sum(lista_capacidades[uc][turno]) <= slots[uc][turno][i][3] for uc in lista_capacidades for turno in lista_capacidades[uc] for i in range(len(slots[uc][turno])) if uc[-2:] == suf_teoria ]

# Aulas sem sobreposicoes
# Percorre todos os alunos e todas as ucs e junta todos os seus turnos num dicionario do tipo de acordo com o seu dia e hora, do tipo {Aluno:{Dia:{Hora:[Ucs]}}}
# Por ultimo, a soma dessa lista com as Ucs num determinado dia, numa determinada hora tem de ser no maximo 1, ou seja, tem de haver no maximo uma alocaçao

turnos = {}
for al in presencas:
    if al not in turnos:
        turnos[al] = {}
    for uc in presencas[al]:
        for t in presencas[al][uc]:
            for d in dias_slots:
                if d not in turnos[al]:
                    turnos[al][d] = {}
                slot_max = dias_slots[d]
                for s in range(slot_max):
                    tuplo = slots[uc][t]
                    for i in range(len(tuplo)):
                        if tuplo[i][0] == d and (tuplo[i][1] <= s <= tuplo[i][2]):
                            if s not in turnos[al][d]:
                                turnos[al][d][s] = []
                            turnos[al][d][s] += [ presencas[al][uc][t] ]
#pprint.pprint(turnos)

sem_sobreposicoes_c = [ Sum(turnos[al][d][s]) <= 1 for al in turnos for d in turnos[al] for s in turnos[al][d] if len(turnos[al][d][s]) > 0 ]

######### grupos #######
#Carrega os grupos e cria a restrição dos grupos 
grupos_c = []
sum_grupos = []
for uc in grupos_json:
    for grupo in grupos_json[uc]:
        al1 = grupos_json[uc][grupo][0]
        grupos_c += [ And([ presencas[al1][uc][t] == presencas[al][uc][t] for al in grupos_json[uc][grupo][1:] ]) for t in presencas[al1][uc] ]
        sum_grupos += [ If(And([ presencas[al1][uc][t] == presencas[al][uc][t] for al in grupos_json[uc][grupo][1:] ]),1,0) for t in presencas[al1][uc] ]

max_grupos = Sum( sum_grupos )
########################### SOLVER ############################
print 'Numero de alunos: %s' % len(alunos)

s = Optimize()

#s.set('timeout', 300000)
x = time.clock()
s.add(values_c)
print 'Solving constraint 0 or 1'
if s.check() != sat:
    print 'Failed to solver constraint 0 or 1'
    sys.exit()
x1 = x
x = time.clock()
print x - x1

s.add(um_turnoTP_c)
print 'Solving constraint obrigatório um turno TP'
if s.check() != sat:
    print 'Failed to solver constraint obrigatório um turno TP'
    sys.exit()
x1 = x
x = time.clock()
print x - x1

s.add(sem_sobreposicoes_c)
print 'Solving constraint sem sobreposicções'
if s.check() != sat:
    print 'Failed to solver constraint sem sobreposicções'
    sys.exit()
x1 = x
x = time.clock()
print x-x1

s.add(um_turnoT_c)
print 'Solving constraint tentar um turno T'
if s.check() != sat:
    print 'Failed to solver constraint tentar um turno t'
    sys.exit()
x1 = x
x = time.clock()
print x - x1

#s.set('timeout', 900000)
 # 2 slots, 900000 sao 15 min
s.add(um_turnoT_c)
s.add(capacidade_maxima_T_c)
s.maximize(max_Teoricas)
print 'A Maximizar os turnos teoricos dentro das capacidades maximas'
if s.check() != sat:
    print 'Failed to maximize turnos teoricos'
    # sys.exit()
x1 = x
x = time.clock()
print x-x1

for c in grupos_c:
    s.add_soft(c)
s.maximize(max_grupos)
print 'Solving constraint dos grupos'
if s.check() != sat:
    print 'Failed to solver constraint dos grupos'
    # sys.exit()
x1 = x
x = time.clock()
print x - x1

s.add(um_turnoTP_c)
s.add(capacidade_maxima_TP_c)
print 'Solving constraint capacidade maxima dos TPs'
if s.check() != sat:
    print 'Failed to solver constraint alocações nos TPs'
    # sys.exit()
x1 = x
x = time.clock()
print x - x1

m = s.model()
r = {}
for al in presencas:
    if al not in r:
        r[al] = {}
    for uc in presencas[al]:
        if uc not in r[al]:
            r[al][uc] = [] 
        for turno in presencas[al][uc]:
            aloc = m.evaluate(presencas[al][uc][turno])
            if aloc == 1:
                r[al][uc] += [turno]

# #alunos alocados a todas as cadeiras que estao inscritos
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
            n_tur += 1
            if t not in alocacoes_finais[u]:
                alocacoes_finais[u][t] = 1
            else:
                alocacoes_finais[u][t] += 1
    if n_tur >= len(r[al]) :
        total_aloc += 1
        n_tur = 0

# #calcular alunos alocados a todas as cadeiras que estao inscritos  
for al in alunos:
    for uc in alunos[al]:
        if not uc[-2:] == suf_teoria and len(r[al][uc]) == 0 and al not in nao_alocados:
            nao_alocados.append(al)
        if uc[-2:] == suf_teoria and len(r[al][uc]) == 0 and al not in nao_alocados_t:
            nao_alocados_t.append(al)

# #calcular os grupos que ficaram juntos ou não
grupos_nao_juntos = []
for uc in grupos_json:
    for grupo in grupos_json[uc]:
        al1 = grupos_json[uc][grupo][0]
        turno = r[al1][uc][0]
        for al in grupos_json[uc][grupo]:
            if turno not in r[al][uc]:
                grupos_nao_juntos += [ uc+'_'+grupo+' : '+al ]

pprint.pprint(alocacoes_finais)
#pprint.pprint(r)
print 'Alunos alocados a todas as ucs: %s' % str(total_aloc)
print 'Alunos não alocados a praticas: '
pprint.pprint(nao_alocados)
print 'Alunos não alocados a teoricas: '
pprint.pprint(nao_alocados_t)
print 'grupos nao juntos: '
pprint.pprint(grupos_nao_juntos)
#print s.statistics()
