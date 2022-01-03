from motorized import QuerySet, Q
from typing import List
from toonbase import AsyncToon
from newtoon import WebToonPacked, Chapter


description = 'Migrate from chapter centric to toon centric implementation'


async def get_migrated_models(queryset: QuerySet = AsyncToon.objects) -> List[WebToonPacked]:
    out = []
    toon_names = await queryset.distinct('name')
    for toon_name in toon_names:
        toon = await queryset.filter(name=toon_name, next=None).first()
        toon_qs = queryset \
            .filter(name=toon_name) \
            .order_by(['created', 'episode'])
        chapters = await toon_qs.distinct('chapter')
        episodes = await toon_qs.distinct('episode')
        chapters_len = len(chapters)
        episodes_len = len(episodes)
        delta = episodes_len - chapters_len
        if delta > 0:
            chapters.extend([None for _ in range(delta)])

        instance = WebToonPacked(
            name=toon.name,
            titleno=getattr(toon, 'titleno', None),
            lang=toon.lang,
            gender=getattr(toon, 'gender', None),
            chapters=[
                Chapter(
                    name=name if name else episode,
                    episode=episode,
                )
                for name, episode in zip(chapters, episodes)
            ],
            finished=toon.finished,
            domain=toon.domain,
            corporate=toon.corporate,
        )
        out.append(instance)
    return out


async def check_for_anomalies(models: List[WebToonPacked], targets: QuerySet) -> None:
    print(targets._query)
    if len(models) != len(await targets.distinct('name')):
        raise Exception('Missing migrations !')


async def apply() -> int:
    targets = AsyncToon.objects \
        .filter(Q(finished=False) | Q(finished__exists=False))

    models = await get_migrated_models(targets)
    await WebToonPacked.objects.drop()
    for model in models:
        await model.save()
    return len(models)


async def revert() -> int:
    impacted_rows = await WebToonPacked.objects.count()
    await WebToonPacked.objects.drop()
    return impacted_rows
