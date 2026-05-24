"""Chunk crawled markdown for RAG via recursive character splitting."""

from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Firecrawl RAG guide defaults: https://www.firecrawl.dev/blog/best-chunking-strategies-rag
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
MARKDOWN_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@lru_cache(maxsize=1)
def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=MARKDOWN_SEPARATORS,
    )


def chunk_markdown(text: str) -> list[str]:
    """Split markdown into overlapping chunks at paragraph, line, and sentence boundaries."""
    stripped = text.strip()
    if not stripped:
        return []
    return _splitter().split_text(stripped)


def chunk_markdown_safe(text: str) -> list[str]:
    """Split markdown; on failure or empty result, return the full text as a single chunk."""
    stripped = text.strip()
    if not stripped:
        return []
    try:
        chunks = chunk_markdown(stripped)
        if chunks:
            return chunks
    except Exception:
        pass
    return [stripped]


SAMPLE_MARKDOWN = """
    Online Investments\n\nStart today with any amount of capital\n\nOpen an account\n\n## Thousands of features in one platform\n\n![Thousands of features in one platform](https://fbroker.kz/file/01KRDHAY8T9J5V48C2E4XJYBYC.png)\n\nFreedom Broker is a multi–market trading terminal. Trade through any browser or free mobile app on iOS and Android.\n\n![Thousands of features in one platform](https://fbroker.kz/file/01KRDHAY8T9J5V48C2E4XJYBYC.png)\n\nModern trading platform\n\nAll exchanges and instruments are available on the same Freedom Broker platform. Invest through a browser on your computer or a mobile app.\n\nA unified multi-currency account\n\nYou can top up your account in any available currency – dollars, tenge, rubles or euros.\n\nA wide range of assets\n\nStocks, bonds, exchange–traded funds ETFs, mutual funds (mutual funds) - thousands of securities are available to you.\n\n## Access to global exchanges\n\n![slide-0](https://fbroker.kz/file/IAIPx1Z5ZaJ5bmm9WhpUQRhpJ3mI8T-metabnlzZS5wbmc%3D-.png)\n\n![slide-1](https://fbroker.kz/file/YOVbhuGh5J4cx4cNLStobeCRw0JIai-metabmFzZGFxLnBuZw%3D%3D-.png)\n\n![slide-2](https://fbroker.kz/file/HHHXjSajwXA4QNzdXVku3k0m35B0BF-metabG9uZG9uLnBuZw%3D%3D-.png)\n\n![slide-3](https://fbroker.kz/file/3KVD4HdNzlFWVVTWxoJa8uu3VCzeNs-metaRGV1dHNjaGVfQm9lcnNlX1hldHJhX0xvZ28gKDEpLW1vZGlmaWVkLnBuZw%3D%3D-.png)\n\n![slide-4](https://fbroker.kz/file/Mh0vWgpUr7TQA6tnjIEihRPnCUnsvS-metaa2FzZS5wbmc%3D-.png)\n\n![slide-5](https://fbroker.kz/file/yHEGxfm6kbEx4kvLR28RzjIy0lENqz-metabGl4LnBuZw%3D%3D-.png)\n\nOpen an account\n\n## ITS: a new look at US and European stocks\n\n### 3000\n\nstocks, depository receipts and ETF\n\n### 19-hour\n\ntrading session (from 9:00 to 3:45 GMT +5)\n\n[More](https://fbroker.kz/products/its)\n\nLearn more at itsx.kz\n\n## Freedom Broker in numbers\n\n#### 18 years in the financial markets\n\nIt has been operating since 2008. The brokerage business is represented in 21 countries and continues to grow.\n\n#### We serve 340 thousand accounts\n\nPeople choose us to achieve their financial goals.\n\n#### 22 minutes is the average account opening time.\n\nSimple registration. A minimum of data and documents. Our record: we opened an account in 2 minutes.\n\n#### 10 largest exchanges with one account\n\nMulti-currency account. Trade on the stock markets of the USA, Europe, the CIS and Asia.\n\n#### $68 billion - clients' trading volume for 2024\\*\n\n\\*Еxcluding repos and derivatives. Investors are actively pursuing their dreams. Join us!\n\n## It's easy to start investing!\n\nThree simple steps\n\nDownload the mobile app\n\n**Freedom**\n\n**Broker**\n\n![Card logo](https://fbroker.kz/file/BCoIfXNfHcqqw60XhG3L1OJYYuOTAI-metaMS5wbmc%3D-.png)\n\n1\n\nOpen the app and\n\nregister\n\n![Card logo](https://fbroker.kz/file/w4dChSssP6f19A9M9UQUW72aff1S4R-metaR3JlZW4gbG9nbyArIFBob25lIDEgKDEpLnBuZw%3D%3D-.png)\n\n2\n\nClick «Open a trading account»\n\n![Card logo](https://fbroker.kz/file/x6fxXRn4I3bBl6YXbUr3DAv9RX6cvP-metaR3JlZW4gbG9nbyArIFBob25lIDEgKDIpLnBuZw%3D%3D-.png)\n\n3\n\nDownload the app\n\nYou can also view the detailed [video guide](https://youtu.be/0IOOoglysXU?si=1lL8p90YMF8LZ9Gc)\n\n### The legal field of the AIFC\n\nFreedom Finance Global PLC is registered in the Astana International Financial Center.\n\n![License](https://fbroker.kz/file/01KGRKKC2Y6MMA264G7AH36PMJ.jpg)\n\nThe legal regime of the IFC is based on the principles of English law and the experience of financial centers in New York, London, Dubai, Hong Kong and Singapore.\n\n![The rights of Freedom Broker investors are protected by international standards. ](https://fbroker.kz/file/ueEgi9La0d6nXxmrUtXfv1ajXWD93B-metaSW5zdGFncmFtLnBuZw%3D%3D-.png)\n\nThe rights of Freedom Broker investors are protected by international standards.\n\n### Proven reliability\n\nFreedom Broker is part of the structure of Freedom Holding Corp. – an American holding company with headquarters in Almaty, Kazakhstan.\n\n![picture-0](https://fbroker.kz/file/01KN3YFPF9SFRYV59VHNP95ZPC.png)\n\n![picture-1](https://fbroker.kz/file/01KN3YFPHP0JR2AM7M8XKD5GMR.png)\n\n![picture-2](https://fbroker.kz/file/01KN3YFPHZ70WBKK3F22DC3MTD.png)\n\n![picture-3](https://fbroker.kz/file/01KN3YFPJFR9D8S747NMVC786W.png)\n\n![Clients' funds are held separately from Freedom Broker's assets](https://fbroker.kz/file/kHwrIpZ8tghS34XAcpP7nd2hUPXsq5-metaSW5zdGFncmFtLnBuZw%3D%3D-.png)\n\nClients' funds are held separately from Freedom Broker's assets\n\n## Proven leadership\n\n![Best Fixed Income Broker (2025, AIX Partners Awards)](https://fbroker.kz/file/01KN3X430V9FQ0FGHY334FPNZV.jpg)\n\nBest Fixed Income Broker (2025, AIX Partners Awards)\n\n![Tech for Finance Excellence (2025, Astana International Financial Center)](https://fbroker.kz/file/01K73RSEBYPN831KC57QQBEG3X.png)\n\nTech for Finance Excellence (2025, Astana International Financial Center)\n\n![Freedom Finance Global PLC – Champion retail brokerage (2024, Astana International Financial Center)](https://fbroker.kz/file/IviJS062VBeK7lJF9jeHMqJmpGht9I-metaa1ZwNnhIYzM4MXk3YVJJeklLcXN1dzZJM0FNUmhSLW1ldGFZV2xtWXlCbWNtVmxaRzl0SURFdWNHNW4tLnBuZw%3D%3D-.png)\n\nFreedom Finance Global PLC – Champion retail brokerage (2024, Astana International Financial Center)\n\n![Best Fixed Income Broker (by Trading Volume) 2024](https://fbroker.kz/file/Q8RkKrQDuPZwZzTCQlYI0LTr4zEVJ3-metaNkoxM29pTURtSmxGTzRjQllWUm1BTjM4b2doU1Z4LW1ldGEwSnpRdnRDOTBZTFFzTkMyMEwzUXNOR1BJTkMrMExIUXU5Q3cwWUhSZ3RHTUlERmZNUzB4TURBdWFuQm4tLmpwZw%3D%3D-.jpg)\n\nBest Fixed Income Broker (by Trading Volume) 2024\n\n![Best Research House (2021, International Finance Awards)](https://fbroker.kz/file/fggun2kcJoBIqiWb3WSFzebcLUZxJx-metaUnI4TVl2UTU5aUxLWmx4a1Q2QWpQRVk4SlpEUWtoLW1ldGFRbVZ6ZENCU1pYTmxZWEpqYUNCSWIzVnpaUzV3Ym1jPS0ucG5n-.png)\n\nBest Research House (2021, International Finance Awards)\n\n![Most Innovative Securities Brokerage (2021, International Finance Awards)](https://fbroker.kz/file/T9ymizGKKw09dp0z4qyTp2uMoyr7cZ-metaN3J5SHBZdE5jREJjZXJiVGxTZ3VvbldIVEVkc2NLLW1ldGFTVzV1YjNaaGRHbDJaUzV3Ym1jPS0ucG5n-.png)\n\nMost Innovative Securities Brokerage (2021, International Finance Awards)\n\n## News\n\nAll\n\n[Stock Market News\\\\\n\\\\\n23 мая 2026, 00:45\\\\\n\\\\\nФондовые индексы США финишировали в умеренном плюсе](https://fbroker.kz/en/news/50184-fondovye-indeksy-ssa-finisirovali-v-umerennom-pliuse-ru-2) [Stock Market News\\\\\n\\\\\n22 мая 2026, 23:47\\\\\n\\\\\nЦены на нефть выросли на фоне медленного прогресса в мирных переговорах между США и Ираном](https://fbroker.kz/en/news/50183-ceny-na-neft-vyrosli-na-fone-medlennogo-progressa-v-mirnyx-peregovorax-mezdu-ssa-i-iranom-ru-2) [Stock Market News\\\\\n\\\\\n22 мая 2026, 23:46\\\\\n\\\\\nАкции Reddit просели на 6% после запуска нового приложения от Meta](https://fbroker.kz/en/news/50182-akcii-reddit-proseli-na-6-posle-zapuska-novogo-prilozeniia-ot-meta-ru-2) [Stock Market News\\\\\n\\\\\n22 мая 2026, 22:50\\\\\n\\\\\nКоличество буровых вышек в США выросло на 7](https://fbroker.kz/en/news/50181-kolicestvo-burovyx-vysek-v-ssa-vyroslo-na-7-ru-2) [Stock Market News\\\\\n\\\\\n22 мая 2026, 22:15\\\\\n\\\\\nFreedom Broker повысил целевую цену aTyr Pharma более чем в 4 раза](https://fbroker.kz/en/news/50179-freedom-broker-povysil-celevuiu-cenu-atyr-pharma-bolee-cem-v-4-raza-ru-2) [Stock Market News\\\\\n\\\\\n22 мая 2026, 22:14\\\\\n\\\\\nFreedom Broker: акции EasyJet испытывают давление из-за снижения спроса](https://fbroker.kz/en/news/50178-freedom-broker-akcii-easyjet-ispytyvaiut-davlenie-iz-za-snizeniia-sprosa-ru-2)\n\n[All materials](https://fbroker.kz/en/news)\n\n## Journal  The financier\n\nA magazine about personal investments, brands and promotions\n\n[Read](https://fbroker.kz/en/journals)\n\n![Journal                       The financier-0](https://fbroker.kz/file/01KRG31YC67XG4N11R5MFN577T.jpg)![Journal                       The financier-1](https://fbroker.kz/file/01KM5QMTE8M12BKBTHCESM82XS.jpg)![Journal                       The financier-2](https://fbroker.kz/file/01KFMW33ZMWQNAWJ6NPZS81TJ9.jpg)\n\n[Read](https://fbroker.kz/en/journals)\n\n## Let us help you invest smarter\n\nArticles for beginners and experienced investors\n\nFor beginners\n\nEverything for a competent start on the stock exchange\n\n[More materials](https://fbroker.kz/en/content/beginner)\n\n![For beginners](https://fbroker.kz/images/main/Beginner.png)\n\nExperienced\n\nAnalytics, investment ideas, advanced articles\n\n[More materials](https://fbroker.kz/en/content/experienced)\n\n![Experienced](https://fbroker.kz/images/main/Expirenced.png)\n\n![Icon](https://fbroker.kz/file/2PeXm9uzUWnbw7uAdSarAd9pTAhqBO-meta0L7QsdGD0YfQtdC90LjQtSAg0LrQvtC_0LjRjy5wbmc%3D-.png)\n\nTraining from Freedom Academy\n\n![Icon](https://fbroker.kz/file/oOgeDrMlEcKbRGkagtYMSSGxlbP5LT-metaVE4g0LrQvtC_0LjRjy5wbmc%3D-.png)\n\nFreedom Broker trading platform\n\n![Icon](https://fbroker.kz/file/w6ykdvF3kSls3jJdI5wvrii9O01XeE-meta0LLQvtC_0YDQvtGB0YsucG5n-.png)\n\nFrequently asked questions, FAQ\n\n[![Рынок США: обзор и прогноз на 22 мая. Вектор торгам задаст геополитика](https://fbroker.kz/file/analytics-images%2F01KS7NFFMNF0222T0CMCHCXN14.png)\\\\\n\\\\\n22 May 2026, 15:56\\\\\n\\\\\nРынок США: обзор и прогноз на 22 мая. Вектор торгам задаст геополитика](https://fbroker.kz/en/analytics/analytics-article/rynok-ssa-obzor-i-prognoz-na-22-maia-vektor-torgam-zadast-geopolitika-ru-2) [![Antero Resources Corporation: независимая нефтегазовая компания](https://fbroker.kz/file/analytics-images%2F01KS2TP5JQ0742NGSMJF4PSA5M.jpg)\\\\\n\\\\\n20 May 2026, 18:52\\\\\n\\\\\nAntero Resources Corporation: независимая нефтегазовая компания](https://fbroker.kz/en/analytics/analytics-article/antero-resources-corporation-nezavisimaia-neftegazovaia-kompaniia-ru-2) [![Рынок США: обзор и прогноз на 20 мая. В фокусе отчет NVIDIA и протоколы FOMC ](https://fbroker.kz/file/analytics-images%2F01KS2EY77W8PRHTTM0ABVAVT53.png)\\\\\n\\\\\n20 May 2026, 15:28\\\\\n\\\\\nРынок США: обзор и прогноз на 20 мая. В фокусе отчет NVIDIA и протоколы FOMC](https://fbroker.kz/en/analytics/analytics-article/rynok-ssa-obzor-i-prognoz-na-20-maia-v-fokuse-otcet-nvidia-i-protokoly-fomc-ru-2)\n\n[More materials](https://fbroker.kz/en/analytics)
"""


def _demo() -> None:
    text = SAMPLE_MARKDOWN.strip()
    chunks = chunk_markdown(text)
    sizes = [len(c) for c in chunks]

    print(f"input: {len(text)} chars")
    print(f"chunks: {len(chunks)} (avg {sum(sizes) // len(sizes) if sizes else 0} chars)\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"--- chunk {i} ({len(chunk)} chars) ---")
        print(chunk[:200] + ("..." if len(chunk) > 200 else ""))
        print()


if __name__ == "__main__":
    _demo()
