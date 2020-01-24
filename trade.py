import re


class TradeOrder:
    def __init__(self, buyerName, itemName, exalts, chaos, stashTab, itemPosition):
        self.buyerName = buyerName
        self.itemName = itemName
        self.exalts = exalts
        self.chaos = chaos
        self.stashTab = stashTab
        self.itemPosition = itemPosition

    def printInfo(self):
        print('Buyer Name: ' + self.buyerName)
        print('Item Name: ' + self.itemName)
        print('Exalts: ' + str(self.exalts))
        print('Chaos: ' + str(self.chaos))
        print('Stash Tab: ' + self.stashTab)
        print('Item Position: ' + str(self.itemPosition))

    def correctItem(self, itemData):

        if not self.itemName in itemData:
            print(itemData)
            return False

        priceNumber = re.search('(?<=Note: ~price ).*?(?= )', itemData)
        if not priceNumber:
            print('No cost found')
            return False
        currency = re.search('(?<=Note: ~price {} ).*?(?=\s)'.format(priceNumber.group(0)), itemData)
        if not currency:
            print('No currency found')
            return False

        priceNumberFloat = float(priceNumber.group(0))

        if priceNumberFloat >= self.exalts and currency.group(0) == 'exa':
            return True
        elif priceNumberFloat >= self.chaos and currency.group(0) == 'chaos':
            return True

        print('Not same cost')
        return False