from nltk.tokenize import sent_tokenize, TextTilingTokenizer

class NlpSentenceChunking:
    def chunk(self, text):
        sentences = sent_tokenize(text)
        return [sentence.strip() for sentence in sentences]

class TopicSegmentationChunking:
    def __init__(self):
        self.tokenizer = TextTilingTokenizer()

    def chunk(self, text):
        return self.tokenizer.tokenize(text)

class SlidingWindowChunking:
    def __init__(self, window_size=100, step=50):
        self.window_size = window_size
        self.step = step

    def chunk(self, text):
        words = text.split()
        chunks = []
        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunks.append(' '.join(words[i:i + self.window_size]))
        return chunks

def chunk_nlp_sentence(text):
    chunker = NlpSentenceChunking()
    chunks = chunker.chunk(text)
    return chunks

def chunk_topic_segmentation(text):
    chunker = TopicSegmentationChunking()
    chunks = chunker.chunk(text)
    return chunks

def chunk_sliding_window(text):
    chunker = SlidingWindowChunking()
    chunks = chunker.chunk(text)
    return chunks

# # Example Usage
# def main():
#     text = """
#     ![Alternate Text](https://kaspi.kz/img/main_logo.svg)\n![](https://kaspi.kz/img/externalImg/2025-phone-3x-n.png)\nСервисы Kaspi.kz \n[ Магазин  Покупки   \nв рассрочку   \nс бесплатной   \nдоставкой  ![](https://kaspi.kz/img/services/service-1.svg) Купить  ](https://kaspi.kz/shop) [ Travel  Авиа и ЖД   \nБилеты   \nпо выгодным   \nценам  ![](https://kaspi.kz/img/services/travel-v2.svg) Купить билеты  ](https://kaspi.kz/kaspitravel) [ Переводы  Без комиссий   \nна Kaspi Gold  ![](https://kaspi.kz/img/services/transfers.svg) Совершить перевод  ](https://kaspi.kz/transfers) Акции  Получайте   \nБонусы   \nи покупайте   \nв рассрочку  ![](https://kaspi.kz/img/services/actions.svg) Узнать об акциях  [ Платежи  Без комиссий,   \nболее 10 000 услуг  ![](https://kaspi.kz/img/services/payments.svg) Оплатить услуги  ](https://kaspi.kz/payments) Объявления  Бесплатные объявления товаров и услуг  ![](https://kaspi.kz/img/services/ads.svg) Подать объявление  Мой Банк  Kaspi Red,   \nДепозиты   \nи кредиты   \nонлайн  ![](https://kaspi.kz/img/services/mybank.svg) Перейти в Мой Банк  Госуслуги  Оформления   \nонлайн, без   \nвизита в ЦОН  ![](https://kaspi.kz/img/services/govservice.svg) Оформить  [ Гид  Расскажем всё   \nо продуктах   \nи сервисах  ![](https://kaspi.kz/img/services/guide.svg) Узнать  ](https://guide.kaspi.kz/client/ru) [ Магазин  Покупки   \nв рассрочку   \nс бесплатной   \nдоставкой  ![](https://kaspi.kz/img/services/service-1.svg) Купить  ](https://kaspi.kz/shop) [ Travel  Авиа и ЖД   \nБилеты   \nпо выгодным   \nценам  ![](https://kaspi.kz/img/services/travel-v2.svg) Купить билеты  ](https://kaspi.kz/kaspitravel) [ Переводы  Без комиссий   \nна Kaspi Gold  ![](https://kaspi.kz/img/services/transfers.svg) Совершить перевод  ](https://kaspi.kz/transfers) Акции  Получайте   \nБонусы   \nи покупайте   \nв рассрочку  ![](https://kaspi.kz/img/services/actions.svg) Узнать об акциях  [ Платежи  Без комиссий,   \nболее 10 000 услуг  ![](https://kaspi.kz/img/services/payments.svg) Оплатить услуги  ](https://kaspi.kz/payments) Объявления  Бесплатные объявления товаров и услуг  ![](https://kaspi.kz/img/services/ads.svg) Подать объявление  Мой Банк  Kaspi Red,   \nДепозиты   \nи кредиты   \nонлайн  ![](https://kaspi.kz/img/services/transfers.svg) Перейти в Мой Банк  Госуслуги  Оформления   \nонлайн, без   \nвизита в ЦОН  ![](https://kaspi.kz/img/services/transfers.svg) Оформить  [ Гид  Расскажем всё   \nо продуктах   \nи сервисах  ![](https://kaspi.kz/img/services/guide.svg) Узнать  ](https://guide.kaspi.kz/client/ru)\nИнтернет-магазин на Kaspi.kz \n[ Телефоны,   \nгаджеты  ![](https://kaspi.kz/img/externalImg/Phone.png) ](https://kaspi.kz/shop/c/smartphones%20and%20gadgets/?source=kaspikz) [ Компьютеры  ![](https://kaspi.kz/img/externalImg/Computer.png) ](https://kaspi.kz/shop/c/computers/?source=kaspikz) [ Обувь  ![](https://kaspi.kz/img/externalImg/Shoes1.png) ](https://kaspi.kz/shop/c/shoes/?source=kaspikz) [ Одежда  ![](https://kaspi.kz/img/externalImg/Clothes1.png) ](https://kaspi.kz/shop/c/fashion/?source=kaspikz) [ Украшения  ![](https://kaspi.kz/img/externalImg/Jewelry.png) ](https://kaspi.kz/shop/c/jewelry%20and%20bijouterie/all/?source=kaspikz) [ Спорт,   \nтуризм  ![](https://kaspi.kz/img/externalImg/Sport1.png) ](https://kaspi.kz/shop/c/sports%20and%20outdoors/?source=kaspikz) [ Красота,   \nздоровье  ![](https://kaspi.kz/img/externalImg/Beauty1.png) ](https://kaspi.kz/shop/c/beauty%20care/?source=kaspikz) [ Товары для   \nживотных  ![](https://kaspi.kz/img/externalImg/Animals.png) ](https://kaspi.kz/shop/c/pet%20goods/?source=kaspikz) [ Подарки, товары   \nдля праздников  ![](https://kaspi.kz/img/externalImg/Holidays.png) ](https://kaspi.kz/shop/c/gifts%20and%20party%20supplies/?source=kaspikz) [ ТВ, Аудио,   \nВидео  ![](https://kaspi.kz/img/externalImg/TV.png) ](https://kaspi.kz/shop/c/tv_audio/?source=kaspikz)\n[ Автотовары  ![](https://kaspi.kz/img/externalImg/Avto.png) ](https://kaspi.kz/shop/c/car%20goods/?source=kaspikz) [ Мебель  ![](https://kaspi.kz/img/externalImg/Furniture1.png) ](https://kaspi.kz/shop/c/furniture/?source=kaspikz) [ Супермаркеты  ![](https://kaspi.kz/img/externalImg/Grocery.png) ](https://kaspi.kz/shop/c/food/?source=kaspikz) [ Строительство, ремонт  ![](https://kaspi.kz/img/externalImg/Hard.png) ](https://kaspi.kz/shop/c/construction%20and%20repair/?source=kaspikz) [ Аптеки  ![](https://kaspi.kz/img/externalImg/Pharmcy.png) ](https://kaspi.kz/shop/c/pharmacy/?source=kaspikz) [ Досуг, книги  ![](https://kaspi.kz/img/externalImg/Hobby.png) ](https://kaspi.kz/shop/c/leisure/?source=kaspikz) [ Канцелярские товары  ![](https://kaspi.kz/img/externalImg/Stat.png) ](https://kaspi.kz/shop/c/office%20and%20school%20supplies/?source=kaspikz) [ Товары для дома и дачи  ![](https://kaspi.kz/img/externalImg/Home.png) ](https://kaspi.kz/shop/c/home/?source=kaspikz) [ Детские товары  ![](https://kaspi.kz/img/externalImg/Kids.png) ](https://kaspi.kz/shop/c/child%20goods/?source=kaspikz) [ Бытовая техника  ![](https://kaspi.kz/img/externalImg/HomeApp.png) ](https://kaspi.kz/shop/c/home%20equipment/?source=kaspikz)\n[ Аксессуары  ![](https://kaspi.kz/img/externalImg/Accessories.png) ](https://kaspi.kz/shop/c/fashion%20accessories/all/?source=kaspikz) Акции  ![](https://kaspi.kz/img/externalImg/Gifts1.png)\nПродукты Kaspi.kz \n[ Kaspi Gold  Переводы,   \nплатежи, снятия   \nбез комиссий  ![](https://kaspi.kz/img/gold.svg) Открыть Kaspi Gold онлайн  ](https://kaspi.kz/gold) [ Kaspi Red+  Покупки в рассрочку 0%   \nв магазинах Вашего   \nгорода  ![](https://kaspi.kz/img/red.svg) Открыть Kaspi Red+ онлайн  ](https://kaspi.kz/kaspired) [ Kaspi Gold для ребенка  Деньги на карманные   \nрасходы и контроль   \nтрат  ![](https://kaspi.kz/img/gold.svg) Открыть Kaspi Gold для ребенка  ](https://kaspi.kz/goldkid) [ Кредит на Покупки  Кредит или   \nрассрочка 0%.   \nОдобрение за 1 минуту.  ![](https://kaspi.kz/img/kredit.svg) Оформить Кредит на Покупки  ](https://kaspi.kz/purchase) [ Kaspi Депозит  Снятия и пополнения   \nбез комиссий. Сумма   \nдепозита от 1 000 ₸.  ![](https://kaspi.kz/img/deposit.svg) Открыть Kaspi Депозит  ](https://kaspi.kz/deposit) [ Кредит Наличными  Одобрение онлайн за   \n1 минуту. До 2,2 млн ₸ на Kaspi Gold.  ![](https://kaspi.kz/img/KN.svg) Получить Кредит Наличными  ](https://kaspi.kz/cashkredit) [ Накопительный Депозит  Высокая ставка.   \nВыплата процентов   \nкаждый месяц.  ![](https://kaspi.kz/img/save_deposit.svg) Открыть Накопительный Депозит  ](https://kaspi.kz/savedeposit) [ Кредит для ИП  До 5 млн тенге.   \nБез залога   \nи документов.  ![](https://kaspi.kz/img/KN_entrep.svg) Оформить Кредит для ИП  ](https://kaspi.kz/cashkreditbiz)\nДля Бизнеса \n![](https://kaspi.kz/img/kaspipay_icon.svg)\nKaspi Pay. Приложение   \nдля бизнеса\nПринимайте оплату с \n![](https://kaspi.kz/img/gold.svg) ![](https://kaspi.kz/img/red.svg) ![](https://kaspi.kz/img/kredit.svg)\n[Подключиться](https://kaspi.kz/kaspipay)\n![](https://kaspi.kz/img/new-entrep-phone-3x.png)\n[ Бизнес Кредит Без залога   \nи документов.   \nОнлайн за 1 минуту  ![](https://kaspi.kz/img/business.svg) Подробнее  ](https://kaspi.kz/bizkredit) [ Акции Kaspi QR Участвуйте в акциях   \nи увеличивайте свои   \nпродажи  ![](https://kaspi.kz/img/actions-sales.svg) Принять участие  ](https://kaspi.kz/marketingactions)\nПринимайте оплату с Kaspi Pay \n![](https://kaspi.kz/img/pos-QR-3x.png)\nSmart POS \n![](https://kaspi.kz/img/mobile-QR-3x.png)\nМобильный POS \n![](https://kaspi.kz/img/display-QR-3x.png)\nQR Дисплей \n[ Принимать оплату с Kaspi Pay ](https://kaspi.kz/kaspipay)\nСтать Партнером \nПродавать   \nв Интернет-магазине   \nна Kaspi.kz \n![](https://kaspi.kz/img/cart.svg)\nБолее 14 млн покупателей,   \nдоставка товаров по всему Казахстану,   \nвозможность продавать в кредит и рассрочку. \n[ Начать продавать в Интернет-магазине ](https://kaspi.kz/shop/merchant/registration/#!/landing)\nПродавать   \nс Kaspi Pay \n![](https://kaspi.kz/img/kaspipay_icon.svg)\nПринимайте оплату с Kaspi Gold, Red+ и Kredit. Откройте счет онлайн бесплатно   \nи получите мобильный POS за 5 минут. \n[ Начать продавать с Kaspi Pay ](https://kaspi.kz/kaspipay)\nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/qr-main-v2.svg)\nМой Банк доступен в мобильном приложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/qr-link-bank-v1.svg)\nОформить Госуслуги   \nВы можете в мобильном приложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/qr-link-gos-v1.svg)\nУзнать об акциях   \nВы можете в мобильном приложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/qr-link-actions-v1.svg)\nПодать объявление,   \nискать товары и услуги   \nвы можете в мобильном   \nприложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/gr-link-obyavleniya.svg)\nНайти отделения  \nВы можете в мобильном  \nприложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/qr-offices-map.png)\nОткрыть Чат с Kaspi Гид   \nВы можете в мобильном   \nприложении Kaspi.kz \nСканируйте, чтобы перейти   \nв приложение Kaspi.kz \n![](https://kaspi.kz/img/QRs/chat-qr.svg)\n
    
# """
#     chunker = NlpSentenceChunking()
#     chunks = chunker.chunk(text)
#     for chunk in chunks:
#         print("--------------------------------")
#         print(chunk)
#     print(len(chunker.chunk(text)))

# if __name__ == "__main__":
#     main()