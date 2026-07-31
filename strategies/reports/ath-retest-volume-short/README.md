# ATH Retest Volume Short

Отдельная short-only стратегия: вход выполняется не на каждом ATH, а после
значительной коррекции и неудачного возврата к прежнему максимуму.

## Сценарий

1. Фиксируется causal ATH.
2. Цена корректируется минимум на `15%` от ATH.
3. Затем high возвращается в пределах `3%` ниже ATH, но не обновляет максимум.
4. На данных от ATH до failed retest строится volume profile из 30 корзин.
5. В верхней половине диапазона выбирается high-volume node с максимальным
   dollar volume.
6. После ухода цены ниже HVN стратегия ждёт обратный retest зоны снизу и
   открывает short по цене node.

Ордер на retest действует 5 дней. Одновременно по символу допускается только
одна позиция или ожидающий сценарий.

## Риск и выход

- Stop-loss: `15%` выше entry.
- Take-profit: `10%`, `15%` или `20%` ниже entry.
- Максимальное удержание: `60 дней`.
- На свече исполнения take-profit запрещён, stop разрешён консервативно.
- Издержки: 14 bps round trip для crypto, 8 bps для акций.

Volume profile является приближённым: весь объём OHLC-свечи относится к её
typical price `(high + low + close) / 3`. Для точного профиля нужны trades или
свечи меньшего таймфрейма.

## Запуск

```bash
PYTHONPATH=src python3 strategies/run_ath_retest_volume_short.py \
  --sector semiconductors \
  --minimum-correction-percent 15 \
  --ath-retest-distance-percent 3 \
  --profile-bins 30 \
  --entry-lifetime-days 5 \
  --take-profit-percent 10 \
  --stop-loss-percent 15
```

## Результаты

[Общая таблица результатов](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
