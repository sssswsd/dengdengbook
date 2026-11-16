# -*- coding: utf-8 -*-
"""故事文本修订：修指代混乱、概念名不一致、写死的章数、重复标题等问题。"""
import json
from pathlib import Path

SEED = Path(__file__).resolve().parent

EDITS = {
    "chapter_ch01.json": {
        "seg1_p10": {
            "body.note": "我说：有四个点，\n只是扣子常有的样子。\n\n它问我：那它为什么叫扣子？\n\n我答不上来。",
        },
        "seg1_p11": {
            "body.lines": ["后来，它认得很准。", "我教过的那些，它一个也没错。"],
            "body.note": "可我没教过的，它一个也认不出来。\n\n我教它什么，它就只学会什么。",
        },
    },
    "chapter_ch02.json": {
        "seg_p01": {"body.kicker": "第四章 · 关于一台会答题的机器"},
        "seg_p10": {
            "body.note": "它不是不会。\n它只是从来没见过一道不一样的题。\n\n下次你想知道一个人会不会，\n别用他做过的题考他。",
        },
    },
    "chapter_ch03.json": {
        "seg3_p01": {"body.note": "我问什么，它都敢答。"},
    },
    "chapter_ch04.json": {
        "seg4_p03": {
            "body.note": "照片上那不是刺猬。\n它有鳞片，会挖洞，舌头很长。\n它叫穿山甲。",
        },
    },
    "chapter_ch05.json": {
        "seg5_p03": {
            "body.lines": ["两张。", "三张。", "它说：斑马。"],
            "body.note": "贴到第三张的时候，它改口了。",
        },
        "seg5_p11": {
            "body.lines": ["它被几道线骗过去，", "这件事有一个名字。"],
            "body.term": "对抗样本",
            "body.term_pinyin": "duì kàng yàng běn",
            "body.definition": "在照片上添几道线，\n它就认成了别的。\n\n这种动过手脚的图，\n叫「对抗样本」。",
            "body.footnote": "它看见的线是真的。\n线是你加的，它不知道。\n\n说它「看走眼」，也行。",
        },
        "__chapter__": {"term": "对抗样本"},
    },
    "chapter_ch07.json": {
        "seg7_p11": {
            "body.lines": [
                "「月亮很圆很圆很圆」——",
                "它盯着「很圆」。",
                "",
                "「鱼在天上游泳」——",
                "它盯着「鱼」「天」「游泳」。",
                "",
                "更要紧的词，它多看几眼。",
                "不要紧的，它就不看。",
            ],
        },
    },
    "chapter_ch08.json": {
        "seg8_p08": {"title": "又过了一天"},
    },
    "chapter_ch09.json": {
        "seg9_p03": {
            "body.lines": ["我问：你怎么知道？", "它说：因为它周围，全是苹果。"],
            "body.note": "我不懂。\n「周围」是什么意思？",
        },
        "seg9_p08": {
            "body.note": "它没记住梨长什么样。\n它只记住梨放在哪儿。",
        },
        "seg9_p09": {
            "body.bubbles": [
                {"q": "它看不见那是梨吗？", "a": "它看见了梨的样子。\n可它不比样子，\n只比谁离得近。"},
                {"q": "那它错了吗？", "a": "按它自己的办法，\n它一点也没错。"},
            ],
        },
    },
    "chapter_ch10.json": {
        "seg10_x_review": {
            "title": "回头看这十二本",
            "body.kicker": "回头看这十二本",
            "body.note": "它推的是你点过的，\n记得住事，记不住你。\n\n这十二本说的是同一件事：\n它一直在你画的那个圈里。",
        },
    },
    "chapter_ch11.json": {
        "seg11_p09": {"body.note": "一块一块，\n拼出它认识的世界。"},
    },
    "chapter_ch12.json": {
        "seg12_p04": {"title": "越长，越忘"},
        "seg12_p08": {"body.note": "后来它换了个办法。\n那是下一章的事。"},
        "seg12_p09": {
            "body.definition": "它一边听，一边把刚听到的\n传给下一步，\n手里只留一点点地方。\n\n大人管这个叫「循环神经网络」，\n简称 RNN。",
            "body.term": "循环神经网络",
            "body.term_pinyin": "xún huán shén jīng wǎng luò",
        },
        "__chapter__": {"term": "循环神经网络"},
    },
}


def set_path(obj, path, value):
    keys = path.split(".")
    cur = obj
    for k in keys[:-1]:
        cur = cur[k]
    cur[keys[-1]] = value


def main():
    changed = 0
    for fname, spec in EDITS.items():
        path = SEED / fname
        data = json.loads(path.read_text(encoding="utf-8"))
        index = {s["id"]: s for s in data["segments"]}

        for sid, fields in spec.items():
            if sid == "__chapter__":
                for f, v in fields.items():
                    data["chapter"][f] = v
                continue
            if sid not in index:
                raise SystemExit(f"未找到段落 {sid} in {fname}")
            seg = index[sid]
            for f, v in fields.items():
                set_path(seg, f, v)
                changed += 1

        # RNN 章 summary 里的旧术语同步
        if fname == "chapter_ch12.json":
            data["summary"] = data["summary"].replace("「循环记忆」", "「循环神经网络」")

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"updated {fname}")
    print(f"total field edits: {changed}")


if __name__ == "__main__":
    main()
