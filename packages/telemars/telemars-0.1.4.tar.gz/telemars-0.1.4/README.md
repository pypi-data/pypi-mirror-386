# telemars

**telemars** — это высокоуровневая, асинхронная библиотека-надстройка для работы с API Mediascope, построенная на базе `mediascope-api-lib`.

Инструмент создан для решения ключевых проблем оригинальной библиотеки: отсутствия валидации данных, медленной работы
и сложности в поддержке кода.

## Установка

```bash
pip install telemars
```

## Конфигурация

Для работы библиотеки необходимо создать файл `settings.json` в корне проекта со следующей структурой:

```json
{
    "username": "YOUR_USERNAME",
    "passw": "YOUR_PASSWORD",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_server": "https://auth.mediascope.net/auth/realms/mediascope/protocol/openid-connect/token",
    "root_url": "https://api.mediascope.net/tvindex/api/v1"
}
```

Данное требование обусловлено особенностями оригинальной библиотеки `mediascope-api-lib`.

**Внимание:** Не забудьте добавить `settings.json` в `.gitignore`, чтобы не допустить утечки конфиденциальных данных.

## Пример использования

```python
import asyncio
from datetime import date
from pprint import pprint

import polars as pl

from telemars.filters import crosstab as filter
from telemars.options.crosstab import Option
from telemars.params.filters import crosstab as cflt
from telemars.params.options import crosstab as cops
from telemars.params.slices.crosstab import Slice
from telemars.params.statistics.crosstab import K7Statistic as Statistic
from telemars.tasks.crosstab import CrosstabTask


async def main() -> pl.DataFrame:
    ct = CrosstabTask(
        date_filter=filter.DateFilter(
            date_from=(date(2025, 1, 1)),
            date_to=date(2025, 1, 31),
        ),
        basedemo_filter=[
            filter.BaseDemoFilter(sex=cflt.Sex.FEMALE, age=(18, 99)),
        ],
        break_filter=filter.BreakFilter(
            breaks_content_type=[cflt.BreaksContentType.COMMERCIAL],
            breaks_issue_status_id=[cflt.BreaksIssueStatusId.REAL],
            breaks_distribution_type=[
                cflt.BreaksDistributionType.NETWORK,
                cflt.BreaksDistributionType.ORBITAL,
            ],
        ),
        platform_filter=filter.PlatformFilter(
            platform_id=[
                cflt.Platform.TV,
                cflt.Platform.DESKTOP,
                cflt.Platform.MOBILE,
            ],
        ),
        playbacktype_filter=filter.PlayBackTypeFilter(
            playback_type_id=[p for p in cflt.PlayBackType],
        ),
        slices=[
            Slice.BREAKS_DISTRIBUTION_TYPE_NAME,
            Slice.TV_COMPANY_NAME,
        ],
        options=Option(
            kit_id=cops.KitId.BIG_TV,
            big_tv=cops.BigTv.YES,
            issue_type=cops.IssueType.BREAKS,
        ),
        sortings=[
            (Slice.BREAKS_DISTRIBUTION_TYPE_NAME, cops.SortOrder.DESC),
            (Slice.TV_COMPANY_NAME, cops.SortOrder.ASC),
        ],
        statistics=[
            Statistic.RTG_PER_AVG,
        ],
    )

    result: pl.DataFrame = await ct.execute()

    pprint(result)


if __name__ == '__main__':
    asyncio.run(main())
```

## Контрибьюция

Предложения по улучшению и доработке проекта приветствуются. Если вы обнаружили проблему или у вас есть идеи по
развитию функционала, пожалуйста, создайте соответствующий Issue.

## Контакты

Email: [prosvirnin.a@outlook.com](mailto:prosvirnin.a@outlook.com)  
Telegram: [@prosvirninjr](https://t.me/prosvirninjr)
