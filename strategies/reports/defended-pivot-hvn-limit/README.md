# Defended Pivot HVN Limit

Отдельная long-only стратегия для уже защищённого weekly pivot с повышенным
относительным объёмом.

После первой защиты строится volume profile в диапазоне `pivot ±1 ATR`:

- окно профиля: первое касание → подтверждение отскока 1.5 ATR;
- 30 ценовых корзин;
- вес: `close × volume`;
- HVN — корзина с максимальным dollar volume.

После следующего пробоя pivot выставляется limit buy в центре HVN. Ордер живёт
5 дней. SL — 25%, TP — 10%/15%/20%, удержание — до 60 дней.

```bash
PYTHONPATH=src python3 strategies/run_defended_pivot_hvn_limit.py \
  --sector crypto --take-profit-percent 10
```

[Общие результаты](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
