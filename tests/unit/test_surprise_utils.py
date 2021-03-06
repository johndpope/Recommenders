# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test utils for Surprise algos
"""
import pandas as pd
import pytest

import surprise

from reco_utils.recommender.surprise.surprise_utils import (
    compute_rating_predictions,
    compute_ranking_predictions
)
from tests.unit.test_python_evaluation import python_data

TOL = 0.001


def test_compute_rating_predictions(python_data):
    rating_true, _, _ = python_data(binary_rating=False)
    svd = surprise.SVD()
    train_set = surprise.Dataset.load_from_df(rating_true, reader=surprise.Reader()).build_full_trainset()
    svd.fit(train_set)

    preds = compute_rating_predictions(svd, rating_true)
    assert set(preds.columns) == {'userID', 'itemID', 'prediction'}
    assert preds['userID'].dtypes == rating_true['userID'].dtypes
    assert preds['itemID'].dtypes == rating_true['itemID'].dtypes
    user = rating_true.iloc[0]['userID']
    item = rating_true.iloc[0]['itemID']
    assert preds[(preds['userID'] == user) & (preds['itemID'] == item)]['prediction'].values == \
           pytest.approx(svd.predict(user, item).est, rel=TOL)

    preds = compute_rating_predictions(svd, rating_true.rename(columns={'userID': 'uid', 'itemID': 'iid'}),
                                       usercol='uid', itemcol='iid', predcol='pred')
    assert set(preds.columns) == {'uid', 'iid', 'pred'}
    assert preds['uid'].dtypes == rating_true['userID'].dtypes
    assert preds['iid'].dtypes == rating_true['itemID'].dtypes
    user = rating_true.iloc[1]['userID']
    item = rating_true.iloc[1]['itemID']
    assert preds[(preds['uid'] == user) & (preds['iid'] == item)]['pred'].values == \
           pytest.approx(svd.predict(user, item).est, rel=TOL)


def test_compute_ranking_predictions(python_data):
    rating_true, _, _ = python_data(binary_rating=False)
    n_users = len(rating_true['userID'].unique())
    n_items = len(rating_true['itemID'].unique())
    svd = surprise.SVD()
    train_set = surprise.Dataset.load_from_df(rating_true, reader=surprise.Reader()).build_full_trainset()
    svd.fit(train_set)

    preds = compute_ranking_predictions(svd, rating_true)
    assert set(preds.columns) == {'userID', 'itemID', 'prediction'}
    assert preds['userID'].dtypes == rating_true['userID'].dtypes
    assert preds['itemID'].dtypes == rating_true['itemID'].dtypes
    user = preds.iloc[0]['userID']
    item = preds.iloc[0]['itemID']
    assert preds[(preds['userID'] == user) & (preds['itemID'] == item)]['prediction'].values == \
           pytest.approx(svd.predict(user, item).est, rel=TOL)
    # Test default recommend_seen=False
    assert pd.merge(rating_true, preds, on=['userID', 'itemID']).shape[0] == 0
    assert preds.shape[0] == (n_users * n_items - rating_true.shape[0])

    preds = compute_ranking_predictions(svd,
                                        rating_true.rename(columns={'userID': 'uid', 'itemID': 'iid', 'rating': 'r'}),
                                        usercol='uid', itemcol='iid', predcol='pred', recommend_seen=True)
    assert set(preds.columns) == {'uid', 'iid', 'pred'}
    assert preds['uid'].dtypes == rating_true['userID'].dtypes
    assert preds['iid'].dtypes == rating_true['itemID'].dtypes
    user = preds.iloc[1]['uid']
    item = preds.iloc[1]['iid']
    assert preds[(preds['uid'] == user) & (preds['iid'] == item)]['pred'].values == \
           pytest.approx(svd.predict(user, item).est, rel=TOL)
    # Test recommend_seen=True
    assert pd.merge(rating_true, preds, left_on=['userID', 'itemID'], right_on=['uid', 'iid']).shape[0] == \
           rating_true.shape[0]
    assert preds.shape[0] == n_users * n_items
