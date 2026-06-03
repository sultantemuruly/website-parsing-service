import os
from dotenv import load_dotenv
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

from langchain.agents import create_agent
from pydantic import BaseModel
from typing import Annotated

class Summary(BaseModel):
    company_name: str
    industry: str
    business_summary: Annotated[str, "The concise and clear summary of the business without any fluff or unnecessary details. Needs to be succinct"]

agent = create_agent(
    model="openai:gpt-5.2",
    system_prompt="You are summary agent. You will be given context about a specific company/business and you will need to summarize it in a concise manner. You will have to give structured output",
    response_format=Summary.model_json_schema(),
)

def main():
    context= """
        [ ![месси](https://bankffin.kz/storage/images/banners/hVRW3iBhQ4pVu8O3HJUaEwEzXyTbONPTKUHzpknm.png) ](https://bankffin.kz/ru/articles/973-igrai-kak-messi-s-mastercard-ot-freedom)\n[ ![прием платежей](https://bankffin.kz/storage/images/banners/vUaxuNdtUS16j7BncKBNCJwA46A8uaeLBZRP2TCX.png) ](https://bankffin.kz/ru/accepting_online_payments)\n[ ![автокред](https://bankffin.kz/storage/images/banners/MOsYURb4G5L2VOgfG3u4kf8iq2KESlzWRj9ANRKq.png) ](https://auto.bankffin.kz/?utm_source=banner&amp;utm_medium=landingru&amp;utm_campaign=bank)\n[ ![лояльность монета](https://bankffin.kz/storage/images/banners/JReteHh4FGmDaRb3udElAwyQ6o5cO1M06mQjwsXQ.png) ](https://loyalty.bankffin.kz/ru?utm_source=site&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_medium=banner&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_campaign=loyalty&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_content=ru)\n[ ![кешбэк за депозит](https://bankffin.kz/storage/images/banners/vR8TMi2Zdofv32P3F397w0TBHj6JJIAYHVjJSTZc.png) ](https://bankffin.kz/ru/articles/824-ucastvuite-v-specpredlozenii-po-vkladam-kapital-i-strategiia)\n[ ![наруто](https://bankffin.kz/storage/images/banners/Etz5ZbZqwvDiMlHN1yyWCeNfNnB6ZOYkoSBB0M9o.png) ](https://naruto.bankffin.kz/ru/)\n[ ![DC.](https://bankffin.kz/storage/images/banners/Zv6qJEHFtwSDavxRnmXVJoFjml2z2KatpD7iXth7.png) ](https://dc.bankffin.kz/ru)\n[ ![RiM](https://bankffin.kz/storage/images/banners/WrhyC5Him3N8kPvduAO7JOmrgvmK6zs5MIWqWElB.png) ](https://rickandmorty.bankffin.kz/ru)\n[ ![Кредит для ТОО](https://bankffin.kz/storage/images/banners/B6XawJ2CAiQgldRDhAITpz31tVj5RzR2C2aWSsZH.png) ](https://corpcredit.bankffin.kz/ru/home)\n[ ![Комплаенс](https://bankffin.kz/storage/images/banners/tLSFTVaP6jQMLRVnM16ndOMyUi3ddcKdErbCez1O.png) ](https://compliance.bankffin.kz/)\n  * 1\n  * 2\n  * 3\n  * 4\n  * 5\n  * 6\n  * 7\n  * 8\n  * 9\n  * 10\n\n\n[ ![месси](https://bankffin.kz/storage/images/banners/vLBha1mz5zELE9whbYoPGlNopwboZrSMoUvcyJaW.png) ](https://bankffin.kz/ru/articles/973-igrai-kak-messi-s-mastercard-ot-freedom)\n[ ![прием платежей](https://bankffin.kz/storage/images/banners/i2NMLuD1ChxCGCj6ptnqfRVrPth2XuuZUFodCQ3J.png) ](https://bankffin.kz/ru/accepting_online_payments)\n[ ![автокред](https://bankffin.kz/storage/images/banners/M5fMYCJodyYgkbLuv9fhtk1dkvmb8gSLxUzfDQzr.png) ](https://auto.bankffin.kz/?utm_source=banner&amp;utm_medium=landingru&amp;utm_campaign=bank)\n[ ![лояльность монета](https://bankffin.kz/storage/images/banners/4oY13pLnFgDf1fVksPmE0zA87vGy0lx3JsPoNcb9.png) ](https://loyalty.bankffin.kz/ru?utm_source=site&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_medium=banner&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_campaign=loyalty&amp;amp;amp;amp;amp;amp;amp;amp;amp;utm_content=ru)\n[ ![кешбэк за депозит](https://bankffin.kz/storage/images/banners/9ApVVGD7kz4fVFmph6lWuONbYFYteqy2qZfQRvxw.png) ](https://bankffin.kz/ru/articles/824-ucastvuite-v-specpredlozenii-po-vkladam-kapital-i-strategiia)\n[ ![наруто](https://bankffin.kz/storage/images/banners/o7yNIaQVoORxIRqDwo6RDMfPjfLLXydIMn28tM4M.png) ](https://naruto.bankffin.kz/ru/)\n[ ![DC.](https://bankffin.kz/storage/images/banners/q3zwJU4NjiWBvvQRYCqpGV7aM5Ypa4sUKtFuppsZ.png) ](https://dc.bankffin.kz/ru)\n[ ![RiM](https://bankffin.kz/storage/images/banners/UMhRX3EiKcAMLsctajK6glwlhqQTrdfHnkb8JpVR.png) ](https://rickandmorty.bankffin.kz/ru)\n[ ![Кредит для ТОО](https://bankffin.kz/storage/images/banners/RL9gMuk4PBjGEjLGnzuEQ40l8RKDl1BAXnHhC4qg.png) ](https://corpcredit.bankffin.kz/ru/home)\n[ ![Комплаенс](https://bankffin.kz/storage/images/banners/Ajzk9g3XmR5gJOgEpvS39G2JXJjQ9u7ImhQdypFu.png) ](https://compliance.bankffin.kz/)\n  * 1\n  * 2\n  * 3\n  * 4\n  * 5\n  * 6\n  * 7\n  * 8\n  * 9\n  * 10\n\n\n# АО «Фридом Банк Казахстан»\n![](https://bankffin.kz/images/invest-card-promo/briefcase-icons/bankffin.svg)\nЯвляется частью крупного холдинга Freedom Holding Corp.\n![](https://bankffin.kz/images/partners/kdif.png)\nУчастник Казахстанского фонда гарантирования депозитов\n![](https://bankffin.kz/images/partners/kase.png)\nУчастник Казахстанской фондовой биржи (KASE)\n![](https://bankffin.kz/images/partners/ffin-kaz.png)\nУчастник ассоциации финансистов Казахстана\n![](https://bankffin.kz/images/partners/swift.png)\nУчастник международных межбанковских систем телекоммуникаций S.W.I.F.T. и REUTERS\n![](https://bankffin.kz/images/partners/visa.png)\nПринципиальный член международных платежных систем VISA International и Mastercard Inc\n![](https://bankffin.kz/images/partners/damu.png)\nЯвляется партнером Фонда развития предпринимательства “Даму”\n![](https://bankffin.kz/images/partners/unistream.svg)\nЯвляется членом международной платёжной системы “Золотая корона”\nПартнеры\n[ ![](https://bankffin.kz/images/security.png) Страхование жизни ](https://ffin.life/?utm_source=bank_ffin_kz) [ ![](https://bankffin.kz/images/calendar.png) Кредиты ](https://ffin.credit/?utm_source=bank_ffin_kz) [ ![](https://bankffin.kz/images/investments.png) Инвестиции ](https://ffin.kz/?utm_source=bank_ffin_kz) [ ![](https://bankffin.kz/images/car.png) Автострахование ](https://ffins.kz/?utm_source=bank_ffin_kz)\n
    """
    response = agent.invoke(
        {"messages": [
            {"role": "user", "content": context}
        ]}
    )
    print(response)

if __name__ == "__main__":
    main()
