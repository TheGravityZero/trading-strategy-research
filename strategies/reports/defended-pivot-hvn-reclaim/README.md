# Defended Pivot HVN Reclaim

Отдельная подтверждающая long-only стратегия на защищённом weekly pivot.

HVN строится по первой защите уровня так же, как в HVN Limit. После следующего
пробоя стратегия не покупает сразу: она ждёт sweep ниже нижней границы HVN и
закрытие свечи обратно выше неё. Вход выполняется по close reclaim-свечи.

Окно ожидания reclaim — 5 дней. SL — 25%, TP — 10%/15%/20%, удержание — до
60 дней.

```bash
PYTHONPATH=src python3 strategies/run_defended_pivot_hvn_reclaim.py \
  --sector crypto --take-profit-percent 10
```

[Общие результаты](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
