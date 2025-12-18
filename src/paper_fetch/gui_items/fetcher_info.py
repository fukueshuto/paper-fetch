import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_fetch.fetchers.arxiv import ArxivFetcher
from paper_fetch.fetchers.ieee import IeeeFetcher
from paper_fetch.fetchers.threegpp import ThreeGPPFetcher
from paper_fetch.fetchers.uspto import UsptoFetcher


def get_fetcher(source):
    if source == "arxiv":
        return ArxivFetcher()
    elif source == "ieee":
        return IeeeFetcher()
    elif source == "3gpp":
        return ThreeGPPFetcher()
    elif source == "uspto":
        return UsptoFetcher()
    return None


def get_search_hint(current_source_for_hint):
    if current_source_for_hint == "arxiv":
        return """
        - **スペース区切り**: OR (いずれかを含む)
        - **AND検索**: `term1 AND term2`
        - **除外**: `term1 ANDNOT term2`
        - **フィールド**: `ti:`(タイトル), `au:`(著者), `abs:`(要旨)
        """
    elif current_source_for_hint == "ieee":
        return """
        - **スペース区切り**: AND (全てを含む)
        - **OR検索**: `term1 OR term2`
        - **除外**: `term1 NOT term2`
        """
    elif current_source_for_hint == "3gpp":
        return """
        - **URL指定**: 会議ドキュメントや仕様書のディレクトリURLを入力してください。
        - 例1: `https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_122b/Docs/`
        - 例2: `https://www.3gpp.org/ftp/Specs/latest/Rel-19/38_series/`
        """
    elif current_source_for_hint == "uspto":
        return """
        - **フレーズ検索**: 単語やフレーズ (Title/Abstract)
        - **日付指定**: `Start Year` / `End Year` を併用
        - **注意**: PatentsView APIを使用。Google Patents形式の検索語とは異なります。
        """
