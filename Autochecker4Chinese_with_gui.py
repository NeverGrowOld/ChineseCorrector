# !/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = "Ainnovation"

import sys
import pinyin
import jieba
import string
import re
import wx
import thulac
import jieba.posseg as pseg

FILE_PATH = "./token_freq_pos%40350k_jieba.txt"
PUNCTUATION_LIST = string.punctuation
PUNCTUATION_LIST += "。，？：；｛｝［］‘“”《》／！％……（） 123456789"

import wx
import wx.lib.pubsub.setupkwargs
from wx.lib.pubsub import pub


def construct_dict(file_path):
    word_freq = {}
    with open(file_path, "r") as f:
        for line in f:
            info = line.split()
            word = info[0]
            frequency = info[1]
            word_freq[word] = frequency
    return word_freq


def load_cn_words_dict(file_path):
    cn_words_dict = ""
    with open(file_path, "r") as f:
        for word in f:
            cn_words_dict += word.strip().decode("utf-8")
    return cn_words_dict


def edits1(phrase, cn_words_dict):
    "All edits that are one edit away from `phrase`."
    phrase = phrase.decode("utf-8")
    splits = [(phrase[:i], phrase[i:]) for i in range(len(phrase) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in cn_words_dict]
    inserts = [L + c + R for L, R in splits for c in cn_words_dict]
    return set(deletes + transposes + replaces + inserts)


def known(phrases): return set(phrase for phrase in phrases if phrase.encode("utf-8") in phrase_freq)


def get_candidates(error_phrase):
    candidates_1st_order = []
    candidates_2nd_order = []
    candidates_3nd_order = []

    error_pinyin = pinyin.get(error_phrase, format="strip", delimiter="/").encode("utf-8")
    cn_words_dict = load_cn_words_dict("./cn_dict.txt")
    candidate_phrases = list(known(edits1(error_phrase, cn_words_dict)))

    for candidate_phrase in candidate_phrases:
        candidate_pinyin = pinyin.get(candidate_phrase, format="strip", delimiter="/").encode("utf-8")
        if candidate_pinyin == error_pinyin:
            candidates_1st_order.append(candidate_phrase)
        elif candidate_pinyin.split("/")[0] == error_pinyin.split("/")[0]:
            candidates_2nd_order.append(candidate_phrase)
        else:
            candidates_3nd_order.append(candidate_phrase)

    return candidates_1st_order, candidates_2nd_order, candidates_3nd_order


def auto_correct(error_phrase):
    c1_order, c2_order, c3_order = get_candidates(error_phrase)
    # print c1_order, c2_order, c3_order
    if c1_order:
        return max(c1_order, key=phrase_freq.get)
    elif c2_order:
        return max(c2_order, key=phrase_freq.get)
    else:
        return max(c3_order, key=phrase_freq.get)


def auto_correct_sentence(error_sentence):
    jieba_cut = jieba.cut(error_sentence.decode("utf-8"), cut_all=False)
    seg_list = "\t".join(jieba_cut).split("\t")

    correct_sentence = ""

    for phrase in seg_list:

        correct_phrase = phrase
        # check if item is a punctuation
        if phrase not in PUNCTUATION_LIST.decode("utf-8"):
            # check if the phrase in our dict, if not then it is a misspelled phrase
            if phrase.encode("utf-8") not in phrase_freq.keys():
                correct_phrase = auto_correct(phrase.encode("utf-8"))
        correct_sentence += correct_phrase
    return correct_sentence


def auto_correct_sentence_thu(error_sentence, verbose=True):
    thu1 = thulac.thulac(seg_only=True, rm_space=True)
    text_cut = thu1.cut(error_sentence.decode("utf-8"), text=True)  # 进行一句话分词
    seg_list_text = "".join(text_cut).split()

    correct_sentence = ""

    for phrase in seg_list_text:

        correct_phrase = phrase.encode("utf-8")
        # check if item is a punctuation
        if phrase not in PUNCTUATION_LIST.decode("utf-8"):
            # check if the phrase in our dict, if not then it is a misspelled phrase
            if phrase.encode("utf-8") not in phrase_freq.keys():
                correct_phrase = auto_correct(phrase.encode("utf-8"))
                if verbose:
                    print(phrase, correct_phrase)

        correct_sentence += correct_phrase

    return correct_sentence

phrase_freq = construct_dict(FILE_PATH)

def cuttest(test_sent):
    thu1 = thulac.thulac()  # 默认模式
    text = thu1.cut(test_sent.decode("utf-8"), text=True)  # 进行一句话分词
    return text

def correction(input_text):
    err_sent_1 = input_text
    print("输入完成:")
    correct_sent = auto_correct_sentence(err_sent_1)
    correct_sent_thulac = auto_correct_sentence_thu(err_sent_1)
    sentence_phraser = cuttest(correct_sent)
    print("检测完成:")
    return correct_sent, correct_sent_thulac,sentence_phraser


########################################################################
class LoginDialog(wx.Dialog):
    """
    Class to define login dialog
    """

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="中文纠错", size=(1200, 1600))

        # input sentence info
        input_sentence = wx.BoxSizer(wx.HORIZONTAL)

        input_sentence_lbl = wx.StaticText(self, -1, "语句输入", wx.Point(0, 10), wx.Size(50, 200))
        input_sentence.Add(input_sentence_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.input_sentence = wx.TextCtrl(self,-1, pos=(5, 160), size=(600, 120), style=wx.TE_MULTILINE | wx.HSCROLL)
        input_sentence.Add(self.input_sentence, 0, wx.ALL, 5)

        # output info -- jieba
        p_sizer = wx.BoxSizer(wx.HORIZONTAL)

        p_lbl = wx.StaticText(self, label="文字纠错--1:") #jieba
        p_sizer.Add(p_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.output = wx.TextCtrl(self, pos=(5, 480), size=(600, 120), style=wx.TE_MULTILINE | wx.HSCROLL)
        p_sizer.Add(self.output, 0, wx.ALL, 5)

        # output info -- thulac
        phraser_thu = wx.BoxSizer(wx.HORIZONTAL)

        phraser_thu_lbl = wx.StaticText(self, label="文字纠错--2:") #thulac
        phraser_thu.Add(phraser_thu_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.output_thu = wx.TextCtrl(self, pos=(5, 320), size=(600, 120), style=wx.TE_MULTILINE | wx.HSCROLL)
        phraser_thu.Add(self.output_thu, 0, wx.ALL, 5)

        # output info -- 分词结果
        phraser_res = wx.BoxSizer(wx.HORIZONTAL)

        phraser_res_lbl = wx.StaticText(self, label="原文分词--1") #jieba
        phraser_res.Add(phraser_res_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.output_phraser_res = wx.TextCtrl(self, pos=(5, 640), size=(600, 120), style=wx.TE_MULTILINE | wx.HSCROLL)
        phraser_res.Add(self.output_phraser_res, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(input_sentence, 0, wx.ALL, 5)
        main_sizer.Add(p_sizer, 0, wx.ALL, 5)
        main_sizer.Add(phraser_thu, 0, wx.ALL, 5)
        main_sizer.Add(phraser_res, 0, wx.ALL, 5)

        btn = wx.Button(self, -1, label="开始纠错",pos=(125, 320), size=(80, 50))
        btn.Bind(wx.EVT_BUTTON, self.onCheck)
        main_sizer.Add(btn, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(main_sizer)

    # ----------------------------------------------------------------------
    def onCheck(self, event):
        """
        Check credentials and login
        """
        inputText = self.input_sentence.GetValue()
        outputText, outputText_Thu, outputText_Phraser = correction(inputText)
        self.output.SetValue(outputText)
        self.output_thu.SetValue(outputText_Thu)
        self.output_phraser_res.SetValue(outputText_Phraser)

########################################################################
class MyPanel(wx.Panel):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)


########################################################################
class MainFrame(wx.Frame):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="Main App")
        panel = MyPanel(self)
        pub.subscribe(self.myListener, "frameListener")

        # Ask user to login
        dlg = LoginDialog()
        dlg.ShowModal()

    # ----------------------------------------------------------------------
    def myListener(self, message, arg2=None):
        """
        Show the frame
        """
        self.Show()


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()