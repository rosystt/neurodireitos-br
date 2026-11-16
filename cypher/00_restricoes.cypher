// Restrições de unicidade: garantem que rodar a carga duas vezes não duplica nós.
CREATE CONSTRAINT pais_nome IF NOT EXISTS FOR (p:Pais) REQUIRE p.nome IS UNIQUE;
CREATE CONSTRAINT empresa_id IF NOT EXISTS FOR (e:Empresa) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT aparelho_id IF NOT EXISTS FOR (a:Aparelho) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT lei_id IF NOT EXISTS FOR (l:Lei) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT criterio_id IF NOT EXISTS FOR (c:Criterio) REQUIRE c.id IS UNIQUE;
