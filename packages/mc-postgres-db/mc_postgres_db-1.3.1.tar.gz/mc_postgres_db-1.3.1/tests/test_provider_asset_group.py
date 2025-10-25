import os
import sys
import datetime as dt
import warnings

import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pytest
import statsmodels.api as sm
from sqlalchemy.orm import Session
from statsmodels.regression.rolling import RollingOLS

from tests.utils import create_base_data
from mc_postgres_db.models import (
    Provider,
    AssetGroupType,
    ProviderAssetGroup,
    ProviderAssetMarket,
    ProviderAssetGroupMember,
    ProviderAssetGroupAttribute,
)
from mc_postgres_db.prefect.tasks import set_data
from mc_postgres_db.testing.utilities import clear_database
from mc_postgres_db.prefect.asyncio.tasks import get_engine as get_engine_async


def create_default_asset_group_type(session: Session) -> AssetGroupType:
    """Helper function to create a default asset group type for testing."""
    asset_group_type = AssetGroupType(
        symbol="DEFAULT_TEST",
        name="Default Test Type",
        description="Default asset group type for testing",
        is_active=True,
    )
    session.add(asset_group_type)
    session.commit()
    session.refresh(asset_group_type)
    return asset_group_type


def generate_ol_data(
    S_0: float, T: pd.date_range, mu: float, theta: float, sigma: float
):
    dt = 1 / len(T)
    S = np.zeros(len(T))
    S[0] = S_0
    for i in range(1, len(T)):
        S[i] = (
            S[i - 1] * np.exp(-mu * dt)
            + theta * (1 - np.exp(-mu * dt))
            + sigma
            * np.sqrt((1 - np.exp(-2 * mu * dt)) / (2 * mu))
            * np.random.normal(0, 1)
        )
    return S


@pytest.mark.asyncio
async def test_create_provider_asset_group_attribute():
    # Get the engine.
    engine = await get_engine_async()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    # Create the time-frame.
    mu = 0.001
    theta = 1
    sigma = 0.01
    window = 60  # 1 hour in minutes
    T = pd.date_range(
        start=dt.datetime.now(),
        end=dt.datetime.now() + dt.timedelta(days=1),
        freq="1min",
    )

    # Create fake market data for the BTC/USD pair.
    starting_price = 10001
    close_prices = generate_ol_data(starting_price, T, mu, theta, sigma)
    fake_market_data_1 = pd.DataFrame(
        {
            "timestamp": T,
            "provider_id": len(T) * [provider.id],
            "from_asset_id": len(T) * [usd_asset.id],
            "to_asset_id": len(T) * [btc_asset.id],
            "close": close_prices,
            "open": close_prices,
            "high": close_prices,
            "low": close_prices,
            "volume": close_prices,
            "best_bid": close_prices,
            "best_ask": close_prices,
        }
    )

    # Create fake market data for the ETH/USD pair.
    starting_price = 300
    close_prices = generate_ol_data(starting_price, T, mu, theta, sigma)
    fake_market_data_2 = pd.DataFrame(
        {
            "timestamp": T,
            "provider_id": len(T) * [provider.id],
            "from_asset_id": len(T) * [usd_asset.id],
            "to_asset_id": len(T) * [eth_asset.id],
            "close": close_prices,
            "open": close_prices,
            "high": close_prices,
            "low": close_prices,
            "volume": close_prices,
            "best_bid": close_prices,
            "best_ask": close_prices,
        }
    )

    # Add the market data to the database.
    set_data(
        ProviderAssetMarket.__tablename__,
        fake_market_data_1,
        operation_type="upsert",
    )
    set_data(
        ProviderAssetMarket.__tablename__,
        fake_market_data_2,
        operation_type="upsert",
    )

    # Create the provider asset group.
    with Session(engine) as session:
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

    # Create the provider asset group members.
    with Session(engine) as session:
        provider_asset_group_member_1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        provider_asset_group_member_2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add(provider_asset_group_member_1)
        session.add(provider_asset_group_member_2)
        session.commit()
        session.refresh(provider_asset_group_member_1)
        session.refresh(provider_asset_group_member_2)

    # Pull the market data for the asset group.
    S_2 = fake_market_data_2["close"].to_numpy()
    S_1 = fake_market_data_1["close"].to_numpy()

    # Calculate the rolling OLS.
    y = S_2
    X = sm.add_constant(S_1)
    rolling_ols = RollingOLS(y, X, window=window)
    results = rolling_ols.fit()

    # Create the provider asset group attribute.
    provider_asset_group_attribute_df = pd.DataFrame(
        {
            "timestamp": T,
            "provider_asset_group_id": len(T) * [provider_asset_group.id],
            "lookback_window_seconds": len(T) * [window * 60],
        }
    )
    provider_asset_group_attribute_df["cointegration_p_value"] = results.pvalues[:, 1]
    provider_asset_group_attribute_df["ou_mu"] = mu
    provider_asset_group_attribute_df["ou_theta"] = theta
    provider_asset_group_attribute_df["ou_sigma"] = sigma
    provider_asset_group_attribute_df["linear_fit_alpha"] = results.params[:, 0]
    provider_asset_group_attribute_df["linear_fit_beta"] = results.params[:, 1]
    provider_asset_group_attribute_df["linear_fit_mse"] = results.mse_resid
    provider_asset_group_attribute_df["linear_fit_r_squared"] = results.rsquared
    provider_asset_group_attribute_df["linear_fit_r_squared_adj"] = results.rsquared_adj
    provider_asset_group_attribute_df = provider_asset_group_attribute_df.dropna()

    # Add the provider asset group attribute to the database.
    set_data(
        ProviderAssetGroupAttribute.__tablename__,
        provider_asset_group_attribute_df,
        operation_type="upsert",
    )


@pytest.mark.asyncio
async def test_create_provider_asset_group_with_members():
    """Test creating a ProviderAssetGroup with multiple ProviderAssetGroupMember entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members to the group
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify the group and its members
        retrieved_group = (
            session.query(ProviderAssetGroup)
            .filter_by(id=provider_asset_group.id)
            .one()
        )
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )

        assert len(members) == 2
        assert retrieved_group.is_active is True


@pytest.mark.asyncio
async def test_composite_primary_key_constraint():
    """Test that composite primary key constraints prevent duplicate entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add a member
        member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        session.add(member)
        session.commit()

        # Attempt to add a duplicate member (same composite key)
        duplicate_member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,  # Same composite key (order is not part of primary key)
        )
        session.add(duplicate_member)

        # Should raise an IntegrityError
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                "New instance.*conflicts with persistent instance",
                category=Warning,
            )
            with pytest.raises(
                Exception
            ):  # SQLite raises Exception, PostgreSQL would raise IntegrityError
                session.commit()
        session.rollback()


@pytest.mark.asyncio
async def test_provider_asset_group_attributes():
    """Test creating and retrieving ProviderAssetGroupAttribute entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Create attributes for different timestamps and lookback windows
        timestamp1 = dt.datetime.now()
        timestamp2 = timestamp1 + dt.timedelta(hours=1)

        attribute1 = ProviderAssetGroupAttribute(
            timestamp=timestamp1,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,  # 1 hour
            cointegration_p_value=0.05,
            ou_mu=0.1,
            ou_theta=0.5,
            ou_sigma=0.2,
            linear_fit_alpha=1.0,
            linear_fit_beta=0.8,
            linear_fit_mse=0.01,
            linear_fit_r_squared=0.95,
            linear_fit_r_squared_adj=0.94,
        )

        attribute2 = ProviderAssetGroupAttribute(
            timestamp=timestamp2,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=7200,  # 2 hours
            cointegration_p_value=0.03,
            ou_mu=0.08,
            ou_theta=0.6,
            ou_sigma=0.15,
            linear_fit_alpha=1.1,
            linear_fit_beta=0.75,
            linear_fit_mse=0.008,
            linear_fit_r_squared=0.97,
            linear_fit_r_squared_adj=0.96,
        )

        session.add_all([attribute1, attribute2])
        session.commit()

        # Retrieve attributes
        retrieved_attr1 = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id,
                lookback_window_seconds=3600,
                timestamp=timestamp1,
            )
            .one()
        )

        retrieved_attr2 = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id,
                lookback_window_seconds=7200,
                timestamp=timestamp2,
            )
            .one()
        )

        # Verify attributes
        assert retrieved_attr1.cointegration_p_value == 0.05
        assert retrieved_attr1.ou_mu == 0.1
        assert retrieved_attr1.linear_fit_alpha == 1.0
        assert retrieved_attr1.linear_fit_r_squared == 0.95

        assert retrieved_attr2.cointegration_p_value == 0.03
        assert retrieved_attr2.ou_mu == 0.08
        assert retrieved_attr2.linear_fit_alpha == 1.1
        assert retrieved_attr2.linear_fit_r_squared == 0.97


@pytest.mark.asyncio
async def test_multiple_providers_same_asset_group():
    """Test that multiple providers can have members in the same asset group."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a second provider
        provider2 = Provider(
            provider_type_id=provider_type.id,
            name="Test Provider 2",
            description="Second test provider",
            is_active=True,
        )
        session.add(provider2)
        session.commit()
        session.refresh(provider2)

        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members from different providers
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider2.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify both providers have members in the same group
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )

        assert len(members) == 2
        provider_ids = {member.provider_id for member in members}
        assert provider.id in provider_ids
        assert provider2.id in provider_ids


@pytest.mark.asyncio
async def test_asset_group_attribute_composite_key():
    """Test that ProviderAssetGroupAttribute composite primary key works correctly."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Create attributes with same timestamp but different lookback windows
        timestamp = dt.datetime.now()

        attribute1 = ProviderAssetGroupAttribute(
            timestamp=timestamp,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,  # 1 hour
            cointegration_p_value=0.05,
        )

        attribute2 = ProviderAssetGroupAttribute(
            timestamp=timestamp,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=7200,  # 2 hours
            cointegration_p_value=0.03,
        )

        session.add_all([attribute1, attribute2])
        session.commit()

        # Verify both attributes exist
        attributes = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id, timestamp=timestamp
            )
            .all()
        )

        assert len(attributes) == 2
        lookback_windows = {attr.lookback_window_seconds for attr in attributes}
        assert 3600 in lookback_windows
        assert 7200 in lookback_windows


@pytest.mark.asyncio
async def test_asset_group_member_relationships():
    """Test the relationships between ProviderAssetGroup, ProviderAssetGroupMember, and ProviderAssetGroupAttribute."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add a member
        member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        session.add(member)
        session.commit()

        # Add an attribute
        attribute = ProviderAssetGroupAttribute(
            timestamp=dt.datetime.now(),
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,
            cointegration_p_value=0.05,
            ou_mu=0.1,
            ou_theta=0.5,
            ou_sigma=0.2,
        )
        session.add(attribute)
        session.commit()

        # Verify relationships work through queries
        # Get all members for this group
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(members) == 1
        assert members[0].from_asset_id == usd_asset.id
        assert members[0].to_asset_id == btc_asset.id

        # Get all attributes for this group
        attributes = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(attributes) == 1
        assert attributes[0].cointegration_p_value == 0.05
        assert attributes[0].ou_mu == 0.1


@pytest.mark.asyncio
async def test_provider_asset_group_member_ordering():
    """Test the optional order column for ProviderAssetGroupMember."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members with explicit ordering
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify ordering
        ordered_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .order_by(ProviderAssetGroupMember.order.asc())
            .all()
        )

        assert len(ordered_members) == 2
        assert ordered_members[0].order == 1
        assert ordered_members[0].to_asset_id == btc_asset.id
        assert ordered_members[1].order == 2
        assert ordered_members[1].to_asset_id == eth_asset.id

        # Test adding a third member with order
        member3 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=btc_asset.id,
            to_asset_id=eth_asset.id,
            order=3,  # Order is now required
        )
        session.add(member3)
        session.commit()

        # Query all members - all should be ordered
        all_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .order_by(ProviderAssetGroupMember.order.asc())
            .all()
        )

        assert len(all_members) == 3
        # All should be ordered
        assert all_members[0].order == 1
        assert all_members[1].order == 2
        assert all_members[2].order == 3


@pytest.mark.asyncio
async def test_provider_asset_group_member_required_ordering():
    """Test that ProviderAssetGroupMember requires an order value."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members with required ordering
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,  # Order is now required
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,  # Order is now required
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify ordering is required and works
        ordered_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .order_by(ProviderAssetGroupMember.order.asc())
            .all()
        )

        assert len(ordered_members) == 2
        # Both should have order values
        assert ordered_members[0].order == 1
        assert ordered_members[1].order == 2


@pytest.mark.asyncio
async def test_provider_asset_group_orm_relationship():
    """Test the ORM relationship between ProviderAssetGroup and ProviderAssetGroupMember."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members to the group
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Test accessing members through the ORM relationship
        # Refresh the group to ensure relationships are loaded
        session.refresh(provider_asset_group)

        # Access members as a list
        members = provider_asset_group.members
        assert len(members) == 2

        # Verify ordering works through the relationship
        assert members[0].order == 1
        assert members[0].to_asset_id == btc_asset.id
        assert members[1].order == 2
        assert members[1].to_asset_id == eth_asset.id

        # Test reverse relationship
        assert member1.group.id == provider_asset_group.id
        assert member2.group.id == provider_asset_group.id

        # Test adding members through the relationship
        member3 = ProviderAssetGroupMember(
            provider_id=provider.id,
            from_asset_id=btc_asset.id,
            to_asset_id=eth_asset.id,
            order=3,
        )
        provider_asset_group.members.append(member3)
        session.commit()

        # Verify the new member was added
        session.refresh(provider_asset_group)
        assert len(provider_asset_group.members) == 3
        assert provider_asset_group.members[2].order == 3
        assert provider_asset_group.members[2].to_asset_id == eth_asset.id


@pytest.mark.asyncio
async def test_provider_asset_group_cascade_delete():
    """Test that deleting a ProviderAssetGroup cascades to its members."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup with members
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify members exist
        members_before = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(members_before) == 2

        # Delete the group
        session.delete(provider_asset_group)
        session.commit()

        # Verify members were cascade deleted
        members_after = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(members_after) == 0


@pytest.mark.asyncio
async def test_orm_member_retrieval_basic():
    """Test basic retrieval of members through ProviderAssetGroup ORM relationship."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add multiple members with different orders
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        member3 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=btc_asset.id,
            to_asset_id=eth_asset.id,
            order=3,
        )
        session.add_all([member1, member2, member3])
        session.commit()

        # Query the group and access members through ORM relationship
        retrieved_group = (
            session.query(ProviderAssetGroup)
            .filter_by(id=provider_asset_group.id)
            .one()
        )

        # Access members through the ORM relationship
        members = retrieved_group.members

        # Verify we got all members
        assert len(members) == 3

        # Verify members are ordered correctly (due to order_by in relationship)
        assert members[0].order == 1
        assert members[1].order == 2
        assert members[2].order == 3

        # Verify member details
        assert members[0].from_asset_id == usd_asset.id
        assert members[0].to_asset_id == btc_asset.id
        assert members[1].from_asset_id == usd_asset.id
        assert members[1].to_asset_id == eth_asset.id
        assert members[2].from_asset_id == btc_asset.id
        assert members[2].to_asset_id == eth_asset.id


@pytest.mark.asyncio
async def test_orm_multiple_groups_member_isolation():
    """Test that multiple groups maintain separate member collections."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create first group with multiple members
        # Create default asset group type
        asset_group_type_1 = create_default_asset_group_type(session)

        provider_asset_group_1 = ProviderAssetGroup(
            asset_group_type_id=asset_group_type_1.id,
            is_active=True,
        )
        session.add(provider_asset_group_1)
        session.commit()
        session.refresh(provider_asset_group_1)

        # Add multiple members to first group
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group_1.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group_1.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Create second group with single member
        # Create another asset group type for the second group
        asset_group_type_2 = AssetGroupType(
            symbol="SECOND_TEST",
            name="Second Test Type",
            description="Second asset group type for testing",
            is_active=True,
        )
        session.add(asset_group_type_2)
        session.commit()
        session.refresh(asset_group_type_2)

        provider_asset_group_2 = ProviderAssetGroup(
            asset_group_type_id=asset_group_type_2.id,
            is_active=True,
        )
        session.add(provider_asset_group_2)
        session.commit()
        session.refresh(provider_asset_group_2)

        # Add one member to the second group
        member3 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group_2.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        session.add(member3)
        session.commit()

        # Query both groups
        groups = (
            session.query(ProviderAssetGroup)
            .filter(
                ProviderAssetGroup.id.in_(
                    [provider_asset_group_1.id, provider_asset_group_2.id]
                )
            )
            .all()
        )

        # Verify each group has the correct number of members
        group1 = next(g for g in groups if g.id == provider_asset_group_1.id)
        group2 = next(g for g in groups if g.id == provider_asset_group_2.id)

        assert len(group1.members) == 2
        assert len(group2.members) == 1

        # Verify the single member in group2
        assert group2.members[0].from_asset_id == usd_asset.id
        assert group2.members[0].to_asset_id == btc_asset.id
        assert group2.members[0].order == 1

        # Verify members in group1
        assert group1.members[0].order == 1
        assert group1.members[1].order == 2


@pytest.mark.asyncio
async def test_orm_bidirectional_relationship():
    """Test that bidirectional relationship works between ProviderAssetGroup and ProviderAssetGroupMember."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        # Create default asset group type
        asset_group_type = create_default_asset_group_type(session)

        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add a member
        member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        session.add(member)
        session.commit()

        # Test forward relationship: group -> members
        retrieved_group = (
            session.query(ProviderAssetGroup)
            .filter_by(id=provider_asset_group.id)
            .one()
        )

        assert len(retrieved_group.members) == 1
        assert retrieved_group.members[0].order == 1

        # Test backward relationship: member -> group
        first_member = retrieved_group.members[0]
        assert first_member.group.id == provider_asset_group.id
        assert first_member.group.id == provider_asset_group.id
        assert first_member.group.is_active is True


@pytest.mark.asyncio
async def test_asset_group_type_creation():
    """Test creation of AssetGroupType instances."""
    engine = await get_engine_async()
    # Clear the database.
    clear_database(engine)

    with Session(engine) as session:
        # Create an AssetGroupType
        asset_group_type = AssetGroupType(
            symbol="PAIRS_TRADING",
            name="Pairs Trading",
            description="Statistical pairs trading for mean reversion strategies",
            is_active=True,
        )
        session.add(asset_group_type)
        session.commit()
        session.refresh(asset_group_type)

        # Verify the asset group type was created
        assert asset_group_type.id is not None
        assert asset_group_type.symbol == "PAIRS_TRADING"
        assert asset_group_type.name == "Pairs Trading"
        assert (
            asset_group_type.description
            == "Statistical pairs trading for mean reversion strategies"
        )
        assert asset_group_type.is_active is True
        assert asset_group_type.created_at is not None
        assert asset_group_type.updated_at is not None


@pytest.mark.asyncio
async def test_asset_group_type_unique_symbol():
    """Test that AssetGroupType symbol must be unique."""
    engine = await get_engine_async()

    # Clear the database.
    clear_database(engine)

    with Session(engine) as session:
        # Create first asset group type
        asset_group_type_1 = AssetGroupType(
            symbol="PAIRS_TRADING",
            name="Pairs Trading",
            description="Statistical pairs trading",
            is_active=True,
        )
        session.add(asset_group_type_1)
        session.commit()

        # Attempt to create second asset group type with same symbol
        asset_group_type_2 = AssetGroupType(
            symbol="PAIRS_TRADING",  # Same symbol
            name="Different Pairs Trading",
            description="Different description",
            is_active=True,
        )
        session.add(asset_group_type_2)

        # Should raise an IntegrityError due to unique constraint
        with pytest.raises(Exception):
            session.commit()


@pytest.mark.asyncio
async def test_provider_asset_group_with_asset_group_type():
    """Test creating ProviderAssetGroup with specific AssetGroupType."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create an AssetGroupType
        asset_group_type = AssetGroupType(
            symbol="ARBITRAGE",
            name="Arbitrage Trading",
            description="Classical arbitrage opportunities",
            is_active=True,
        )
        session.add(asset_group_type)
        session.commit()
        session.refresh(asset_group_type)

        # Create ProviderAssetGroup with the asset group type
        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=asset_group_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Verify the group was created with correct asset group type
        assert provider_asset_group.id is not None
        assert provider_asset_group.asset_group_type_id == asset_group_type.id
        assert provider_asset_group.is_active is True


@pytest.mark.asyncio
async def test_provider_asset_group_requires_asset_group_type():
    """Test that ProviderAssetGroup requires a valid asset_group_type_id."""
    engine = await get_engine_async()

    with Session(engine) as session:
        # Attempt to create ProviderAssetGroup without asset_group_type_id
        provider_asset_group = ProviderAssetGroup(
            is_active=True,
        )
        session.add(provider_asset_group)

        # Should raise an IntegrityError due to foreign key constraint
        with pytest.raises(Exception):
            session.commit()


@pytest.mark.asyncio
async def test_multiple_asset_group_types():
    """Test creating multiple AssetGroupType instances."""
    engine = await get_engine_async()

    # Clear the database.
    clear_database(engine)

    with Session(engine) as session:
        # Create multiple asset group types
        pairs_trading = AssetGroupType(
            symbol="PAIRS_TRADING",
            name="Pairs Trading",
            description="Statistical pairs trading",
            is_active=True,
        )

        arbitrage = AssetGroupType(
            symbol="ARBITRAGE",
            name="Arbitrage Trading",
            description="Classical arbitrage",
            is_active=True,
        )

        triangular_arbitrage = AssetGroupType(
            symbol="TRIANGULAR_ARBITRAGE",
            name="Triangular Arbitrage",
            description="Triangular arbitrage opportunities",
            is_active=True,
        )

        session.add_all([pairs_trading, arbitrage, triangular_arbitrage])
        session.commit()

        # Verify all were created
        assert pairs_trading.id is not None
        assert arbitrage.id is not None
        assert triangular_arbitrage.id is not None

        # Verify unique symbols
        assert pairs_trading.symbol == "PAIRS_TRADING"
        assert arbitrage.symbol == "ARBITRAGE"
        assert triangular_arbitrage.symbol == "TRIANGULAR_ARBITRAGE"


@pytest.mark.asyncio
async def test_asset_group_type_inactive_status():
    """Test AssetGroupType inactive status functionality."""
    engine = await get_engine_async()

    # Clear the database.
    clear_database(engine)

    with Session(engine) as session:
        # Create inactive asset group type
        inactive_type = AssetGroupType(
            symbol="INACTIVE_TYPE",
            name="Inactive Type",
            description="This type is inactive",
            is_active=False,
        )
        session.add(inactive_type)
        session.commit()
        session.refresh(inactive_type)

        # Verify inactive status
        assert inactive_type.is_active is False

        # Create ProviderAssetGroup with inactive type (should still work)
        provider_asset_group = ProviderAssetGroup(
            asset_group_type_id=inactive_type.id,
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Verify the group was created successfully
        assert provider_asset_group.asset_group_type_id == inactive_type.id


@pytest.mark.asyncio
async def test_asset_group_type_query_by_symbol():
    """Test querying AssetGroupType by symbol."""
    engine = await get_engine_async()

    # Clear the database.
    clear_database(engine)

    with Session(engine) as session:
        # Create asset group types
        pairs_trading = AssetGroupType(
            symbol="PAIRS_TRADING",
            name="Pairs Trading",
            description="Statistical pairs trading",
            is_active=True,
        )

        arbitrage = AssetGroupType(
            symbol="ARBITRAGE",
            name="Arbitrage Trading",
            description="Classical arbitrage",
            is_active=True,
        )

        session.add_all([pairs_trading, arbitrage])
        session.commit()

        # Query by symbol
        pairs_type = (
            session.query(AssetGroupType).filter_by(symbol="PAIRS_TRADING").one()
        )
        arbitrage_type = (
            session.query(AssetGroupType).filter_by(symbol="ARBITRAGE").one()
        )

        # Verify correct types were retrieved
        assert pairs_type.name == "Pairs Trading"
        assert arbitrage_type.name == "Arbitrage Trading"


@pytest.mark.asyncio
async def test_provider_asset_group_with_different_types():
    """Test creating ProviderAssetGroup instances with different AssetGroupType."""
    engine = await get_engine_async()

    # Clear the database.
    clear_database(engine)

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create different asset group types
        pairs_trading = AssetGroupType(
            symbol="PAIRS_TRADING",
            name="Pairs Trading",
            description="Statistical pairs trading",
            is_active=True,
        )

        arbitrage = AssetGroupType(
            symbol="ARBITRAGE",
            name="Arbitrage Trading",
            description="Classical arbitrage",
            is_active=True,
        )

        session.add_all([pairs_trading, arbitrage])
        session.commit()

        # Create ProviderAssetGroup instances with different types
        pairs_group = ProviderAssetGroup(
            asset_group_type_id=pairs_trading.id,
            is_active=True,
        )

        arbitrage_group = ProviderAssetGroup(
            asset_group_type_id=arbitrage.id,
            is_active=True,
        )

        session.add_all([pairs_group, arbitrage_group])
        session.commit()

        # Verify groups have correct types
        assert pairs_group.asset_group_type_id == pairs_trading.id
        assert arbitrage_group.asset_group_type_id == arbitrage.id

        # Query and verify
        retrieved_pairs_group = (
            session.query(ProviderAssetGroup)
            .filter_by(asset_group_type_id=pairs_trading.id)
            .one()
        )

        retrieved_arbitrage_group = (
            session.query(ProviderAssetGroup)
            .filter_by(asset_group_type_id=arbitrage.id)
            .one()
        )

        assert retrieved_pairs_group.asset_group_type_id == pairs_trading.id
        assert retrieved_arbitrage_group.asset_group_type_id == arbitrage.id
