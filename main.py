import queue
import re
import keyboard
import threading
import time
import math
import win32.win32clipboard as win32cp
import pyautogui as pag

from playsound import playsound
from trade import TradeOrder

buyOrders = queue.Queue()
playersInArea = set()
stopThreads = False
exaltsToChaos = 160.0
tradeAccepted = False

topLeftQuadStash = [28, 174]
topLeftStash = [44, 188]
topLeftTrade = [338, 230]
quadSquareSize = [27, 26]
squareSize = [52, 53]

def ctrlcToExalts(line):
    isExalted = re.search('Rarity: Currency Exalted Orb --------', line)
    if isExalted:
        stackSize = re.search('(?<=-------- Stack Size: ).*?(?=/10)', line)
        if stackSize:
            return float(stackSize.group(0))
        else:
            print('Exalted stacksize not found...')

    return 0.0


def ctrlcToChaos(line):
    isChaos = re.search('Rarity: Currency Chaos Orb --------', line)
    if isChaos:
        stackSize = re.search('(?<=-------- Stack Size: ).*?(?=/10)', line)
        if stackSize:
            return float(stackSize.group(0))
        else:
            print('Chaos stacksize not found...')

    return 0.0

def parseLine(line):
    global playersInArea
    global tradeAccepted
    isBuyOrder = re.search('Hi, I would like to buy your .* listed for .* \(stash tab .* position: left .*, top .*\)', line)
    playerEnteredAreaName = re.search('(?<=: ).*?(?= has joined the area.)', line)
    playerLeftAreaName = re.search('(?<=: ).*?(?= has left the area.)', line)
    tradeAcceptedRegex = re.search(': Trade accepted.', line)
    if isBuyOrder:
        league = re.search('in Metamorph', line)
        if not league:
            print('Wrong League!')
            return
        buyerName = re.search('(?<=From ).*?(?=:)', line)
        if not buyerName:
            print('buyerName could not be parsed!')
            return
        itemName = re.search('(?<=Hi, I would like to buy your ).*?(?= listed)', line)
        if not itemName:
            print('itemName could not be parsed!')
            return
        priceNumber = re.search('(?<=listed for ).*?(?= )', line)
        if not priceNumber:
            print('priceNumber could not be parsed!')
            return
        currency = re.search('(?<=listed for {} ).*?(?= )'.format(priceNumber.group(0)), line)
        if not currency:
            print('currency could not be parsed!')
            return
        stashTab = re.search('(?<=\(stash tab ").*?(?=";)', line)
        if not stashTab:
            print('stashTab could not be parsed!')
            return
        left = re.search('(?<=position: left ).*?(?=,)', line)
        if not left:
            print('left could not be parsed!')
            return
        top = re.search('(?<=position: left {}, top ).*?(?=\))'.format(left.group(0)), line)
        if not top:
            print('top could not be parsed!')
            return
        buyerNameString = buyerName.group(0)
        itemNameString = itemName.group(0)
        priceNumberString = priceNumber.group(0)
        currencyString = currency.group(0)
        exalts = float(0)
        chaos = float(0)

        if currencyString == 'exa':
            exalts = float(priceNumberString)
        elif currencyString == 'chaos':
            chaos = float(priceNumberString)
        else:
            print('Currency could not be parsed: ' + currencyString)
            return

        stashTabString = stashTab.group(0)
        if stashTabString != 'Quad':
            return

        itemPosition = [int(left.group(0)), int(top.group(0))]

        order = TradeOrder(buyerNameString, itemNameString, exalts, chaos, stashTabString, itemPosition)
        order.printInfo()
        return order
    elif playerEnteredAreaName:
        playersInArea.add(playerEnteredAreaName.group(0))
        print('|' + playerEnteredAreaName.group(0) + '| has entered')
    elif playerLeftAreaName:
        playersInArea.discard(playerLeftAreaName.group(0))
        print(playerLeftAreaName.group(0) + 'has left')
    elif tradeAcceptedRegex:
        tradeAccepted = True

def buyOrderExists(newBuyOrder):
    for buyOrder in buyOrders:
        if buyOrder.itemName == newBuyOrder.itemName and buyOrder.stashTab == newBuyOrder.stashTab and buyOrder.itemPosition == newBuyOrder.itemPosition:
            return True

    return False

def pollingFunc():
    global buyOrders
    global stopThreads

    standalonePath = 'C:\\Program Files (x86)\\Grinding Gear Games\\Path of Exile\\logs\\'
    steamPath = 'D:\\SteamLibrary\\steamapps\\common\\Path of Exile\\logs\\'
    path = steamPath
    fileName = 'Client.txt'
    file = open(path + fileName, 'r', encoding='utf8')
    file.seek(0, 2)

    while not stopThreads:
        line = file.readline()
        if line:
            buyOrder = parseLine(line)
            if buyOrder:
                if not buyOrderExists(buyOrder):
                    time.sleep(2)
                    buyOrders.put(buyOrder)

    file.close()
    print('Thread Dying')

def clearChat():
    pag.keyDown('enter')
    pag.keyUp('enter')
    pag.hotkey('ctrl', 'a')
    pag.keyDown('delete')
    pag.keyUp('delete')

def isTradeAcceptable(exaltsThatShouldBeInTrade, chaosThatShouldBeInTrade):
    exaltsInTrade = 0
    chaosInTrade = 0
    tradeAcceptable = False
    i = 0

    while exaltsInTrade < exaltsThatShouldBeInTrade or chaosInTrade < chaosThatShouldBeInTrade or i < 3:
        i += 1
        exaltsInTrade = 0
        chaosInTrade = 0
        for x in range(12):
            for y in range(5):
                pag.moveTo(topLeftTrade[0] + squareSize[0] * x,
                           topLeftTrade[1] + squareSize[1] * y)
                if not tradeAcceptable:
                    pag.hotkey('ctrl', 'c')
                    win32cp.OpenClipboard()
                    data = win32cp.GetClipboardData()
                    win32cp.CloseClipboard()
                    data = data.replace('\r\n', ' ')
                    data = data.replace('\n', ' ').replace('\r', ' ')
                    exaltsInTrade += ctrlcToExalts(data)  # Todo: What if exalted instead of chaos
                    chaosInTrade += ctrlcToChaos(data)

                    if exaltsInTrade >= exaltsThatShouldBeInTrade and chaosInTrade >= chaosThatShouldBeInTrade:
                        tradeAcceptable = True
                        break

    return tradeAcceptable

def main():
    global buyOrders
    global stopThreads
    global playersInArea
    global tradeAccepted

    pollingThread = threading.Thread(target=pollingFunc, daemon=True)
    pollingThread.start()

    #Todo: What if already in party
    #Todo: What if already in area

    while True:
        if not buyOrders.empty():
            currentBuyOrder = buyOrders.get()
            pag.moveTo(topLeftQuadStash[0] + quadSquareSize[0] * (currentBuyOrder.itemPosition[0] - 1),
                       topLeftQuadStash[1] + quadSquareSize[1] * (currentBuyOrder.itemPosition[1] - 1))

            pag.hotkey('ctrl', 'c')
            win32cp.OpenClipboard()
            data = win32cp.GetClipboardData()
            win32cp.CloseClipboard()
            data = data.replace('\r\n', ' ')
            data = data.replace('\n', ' ').replace('\r', ' ')
            isCorrectItem = currentBuyOrder.correctItem(data)

            if not isCorrectItem:
                return

            #time.sleep(2)

            pag.keyDown('ctrl')
            pag.click()
            pag.keyUp('ctrl')

            clearChat()

            win32cp.OpenClipboard()
            win32cp.EmptyClipboard()
            win32cp.SetClipboardText('/invite ' + currentBuyOrder.buyerName)
            win32cp.CloseClipboard()
            pag.hotkey('ctrl', 'v')
            pag.press('enter')

            playerGoingToAreaCounter = 0
            while currentBuyOrder.buyerName not in playersInArea and playerGoingToAreaCounter < 30: #Todo: This needs a timeout
                playerGoingToAreaCounter += 1
                print('|' + currentBuyOrder.buyerName + '| Not in area yet...')
                time.sleep(0.5)

            if currentBuyOrder.buyerName in playersInArea:
                print('In Area!')
                time.sleep(2)

                clearChat()

                win32cp.OpenClipboard()
                win32cp.EmptyClipboard()
                win32cp.SetClipboardText('/tradewith ' + currentBuyOrder.buyerName)
                win32cp.CloseClipboard()
                pag.hotkey('ctrl', 'v')
                pag.press('enter')

                tradeWindowOpened = False

                while not tradeWindowOpened:
                    try:
                        tradeWindowOpened = pag.locateOnScreen('trade.png', confidence=0.99)
                    except pag.ImageNotFoundException:
                        time.sleep(0.5)

                #time.sleep(10)

                pag.moveTo(1296, 614)
                pag.keyDown('ctrl')
                pag.click()
                pag.keyUp('ctrl')

                exaltsThatShouldBeInTrade = math.floor(currentBuyOrder.exalts)
                chaosThatShouldBeInTrade = currentBuyOrder.chaos + (currentBuyOrder.exalts - exaltsThatShouldBeInTrade) * exaltsToChaos

                acceptTrade = isTradeAcceptable(exaltsThatShouldBeInTrade, chaosThatShouldBeInTrade)

                if acceptTrade:

                    pag.moveTo(374, 836)
                    pag.click()

                    i = 0

                    while not tradeAccepted and i < 20: #Todo this doesnt work
                        i += 1

                        try:
                            pag.locateOnScreen('countdown.png', confidence=0.99)
                            acceptTrade = isTradeAcceptable(exaltsThatShouldBeInTrade, chaosThatShouldBeInTrade)
                            if acceptTrade:
                                playsound('acceptTrade.mp3')
                                #pag.moveTo(374, 836)
                                #pag.click()
                            else:
                                break
                        except pag.ImageNotFoundException:
                            time.sleep(0.5)

                    tradeAccepted = False

                clearChat()

                win32cp.OpenClipboard()
                win32cp.EmptyClipboard()
                win32cp.SetClipboardText('/kick ' + currentBuyOrder.buyerName)
                win32cp.CloseClipboard()
                pag.hotkey('ctrl', 'v')
                pag.press('enter')

        if keyboard.is_pressed('q'):
            stopThreads = True
            pollingThread.join(2)
            return

main()
