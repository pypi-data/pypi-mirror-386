# romkan2

**romkan2** is a modernized, actively maintained fork of [python-romkan](https://github.com/soimort/python-romkan), designed as a **drop-in replacement** for the original library.

This is a Romaji/Kana conversion library for Python, which is used to convert a Japanese Romaji (ローマ字) string to a Japanese Kana (仮名) string or vice versa.

## Why romkan2?

The original [python-romkan](https://github.com/soimort/python-romkan) by Mort Yao has not been actively maintained in recent years. This fork aims to:

- Support modern Python versions (3.9+)
- Modernize the codebase with type hints and improved code structure
- Use contemporary Python packaging standards (pyproject.toml)
- Maintain full backward compatibility as a drop-in replacement

## Heritage

This library is the Pythonic port of [Ruby/Romkan](http://0xcc.net/ruby-romkan/index.html.en), originally authored by Satoru Takabayashi and [ported](http://lilyx.net/python-romkan/) by Masato Hagiwara, then modernized by Mort Yao.

romkan2 handles both Katakana (片仮名) and Hiragana (平仮名) with the Hepburn (ヘボン式) romanization system, as well as the modern Kunrei-shiki (訓令式) romanization system.



## Installation

Install via pip:

```bash
pip install romkan2
```

Or install from source:

```bash
git clone https://github.com/altescy/romkan2.git
cd romkan2
pip install -e .


```

## Usage

```python
import romkan2

# Convert Kana to Romaji
print(romkan2.to_roma("にんじゃ"))
# => ninja

print(romkan2.to_hepburn("にんじゃ"))
# => ninja

print(romkan2.to_kunrei("にんじゃ"))
# => ninzya

# Convert Romaji to Kana
print(romkan2.to_hiragana("ninja"))
# => にんじゃ

print(romkan2.to_katakana("ninja"))
# => ニンジャ
```



## API Reference

### `to_katakana(string: str) -> str`

Convert a Romaji (ローマ字) to a Katakana (片仮名).

### `to_hiragana(string: str) -> str`

Convert a Romaji (ローマ字) to a Hiragana (平仮名).

### `to_kana(string: str) -> str`

Convert a Romaji (ローマ字) to a Katakana (片仮名). (same as `to_katakana`)

### `to_hepburn(string: str) -> str`

Convert a Kana (仮名) or a Kunrei-shiki Romaji (訓令式ローマ字) to a Hepburn Romaji (ヘボン式ローマ字).

### `to_kunrei(string: str) -> str`

Convert a Kana (仮名) or a Hepburn Romaji (ヘボン式ローマ字) to a Kunrei-shiki Romaji (訓令式ローマ字).

### `to_roma(string: str) -> str`

Convert a Kana (仮名) to a Hepburn Romaji (ヘボン式ローマ字).



## Migration from python-romkan

romkan2 is a drop-in replacement for python-romkan. Simply replace:

```python
# Old
import romkan

# New
import romkan2 as romkan
```

## License

romkan2 is licensed under the [BSD license](LICENSE).

## Credits

- Original Ruby/Romkan: [Satoru Takabayashi](http://0xcc.net/ruby-romkan/index.html.en)
- Python port: [Masato Hagiwara](http://lilyx.net/python-romkan/)
- python-romkan: [Mort Yao](https://github.com/soimort/python-romkan)
- romkan2 (this fork): [Yasuhiro Yamaguchi](https://github.com/altescy)
