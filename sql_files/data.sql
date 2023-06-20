-- Экспортная упаковка
INSERT INTO bet (id, name, rate) VALUES (1, 'Экспортная упаковка', 1.6);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'EXW', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'FCA', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'FAS', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (1, 'DDP', 'SELLER');


-- Складские / погрузочные расходы в пункте отправки груза
INSERT INTO bet (id, name, rate) VALUES (2, 'Складские / погрузочные расходы в пункте отправки груза', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'FCA', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'FAS', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (2, 'DDP', 'SELLER');


-- Перевозка до промежуточного пункта отправки груза
INSERT INTO bet (id, name, rate) VALUES (3, 'Перевозка до промежуточного пункта отправки груза', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'FCA', 'ALL');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'FAS', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (3, 'DDP', 'SELLER');


-- Экспортные формальности
INSERT INTO bet (id, name, rate) VALUES (4, 'Экспортные формальности', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'FCA', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'FAS', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (4, 'DDP', 'SELLER');


-- Расходы первичного терминала отправки груза
INSERT INTO bet (id, name, rate) VALUES (5, 'Расходы первичного терминала отправки груза', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (5, 'DDP', 'SELLER');


-- Погрузка на транспортное средство экспортера
INSERT INTO bet (id, name, rate) VALUES (6, 'Погрузка на транспортное средство экспортера', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (6, 'DDP', 'SELLER');


-- Морской / воздушный фрахт (основной способ перевозки)
INSERT INTO bet (id, name, rate) VALUES (7, 'Морской / воздушный фрахт (основной способ перевозки)', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (7, 'DDP', 'SELLER');


-- Расходы экспедитора в пункте назначения
INSERT INTO bet (id, name, rate) VALUES (8, 'Расходы экспедитора в пункте назначения', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'CFR', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'CIF', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'CPT', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'CIP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (8, 'DDP', 'SELLER');


-- Складские / погрузочные расходы в пункте назначения
INSERT INTO bet (id, name, rate) VALUES (9, 'Складские / погрузочные расходы в пункте назначения', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'CFR', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'CIF', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'DPU', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'DAP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'CPT', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'CIP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (9, 'DDP', 'SELLER');


-- Составление документов по безопасности перевозимого груза
INSERT INTO bet (id, name, rate) VALUES (10, 'Составление документов по безопасности перевозимого груза', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'CFR', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'CIF', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'DPU', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'DAP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'CPT', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'CIP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (10, 'DDP', 'SELLER');


-- Таможенные формальности
INSERT INTO bet (id, name, rate) VALUES (11, 'Таможенные формальности', 1.8);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'CFR', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'CIF', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'DPU', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'DAP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'CPT', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'CIP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (11, 'DDP', 'SELLER');


-- Таможенные пошлины и налоги на вывоз груза
INSERT INTO bet (id, name, rate) VALUES (12, 'Таможенные пошлины и налоги на вывоз груза', 2.3);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'FCA', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'FAS', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'FOB', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'CFR', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'CIF', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'DPU', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'DAP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'CPT', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'CIP', 'SELLER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (12, 'DDP', 'SELLER');


-- Таможенные пошлины и налоги на ввоз груза
INSERT INTO bet (id, name, rate) VALUES (13, 'Таможенные пошлины и налоги на ввоз груза', 2.3);

INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'EXW', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'FCA', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'FAS', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'FOB', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'CFR', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'CIF', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'DPU', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'DAP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'CPT', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'CIP', 'BUYER');
INSERT INTO bet_incoterm (bet_id, name, role ) VALUES (13, 'DDP', 'SELLER');
