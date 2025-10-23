import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Tuple

from epyxid import XID
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from intentkit.models.agent import Agent
from intentkit.models.agent_data import AgentData
from intentkit.models.app_setting import AppSetting
from intentkit.models.credit import (
    DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
    DEFAULT_PLATFORM_ACCOUNT_DEV,
    DEFAULT_PLATFORM_ACCOUNT_FEE,
    DEFAULT_PLATFORM_ACCOUNT_MEMORY,
    DEFAULT_PLATFORM_ACCOUNT_MESSAGE,
    DEFAULT_PLATFORM_ACCOUNT_RECHARGE,
    DEFAULT_PLATFORM_ACCOUNT_REFILL,
    DEFAULT_PLATFORM_ACCOUNT_REWARD,
    DEFAULT_PLATFORM_ACCOUNT_SKILL,
    DEFAULT_PLATFORM_ACCOUNT_WITHDRAW,
    CreditAccount,
    CreditAccountTable,
    CreditDebit,
    CreditEvent,
    CreditEventTable,
    CreditTransactionTable,
    CreditType,
    Direction,
    EventType,
    OwnerType,
    RewardType,
    TransactionType,
    UpstreamType,
)
from intentkit.models.db import get_session
from intentkit.models.skill import Skill
from intentkit.utils.error import IntentKitAPIError
from intentkit.utils.slack_alert import send_slack_message

logger = logging.getLogger(__name__)

# Define the precision for all decimal calculations (4 decimal places)
FOURPLACES = Decimal("0.0001")


async def update_credit_event_note(
    session: AsyncSession,
    event_id: str,
    note: Optional[str] = None,
) -> CreditEvent:
    """
    Update the note of a credit event.

    Args:
        session: Async session to use for database operations
        event_id: ID of the event to update
        note: New note for the event

    Returns:
        Updated credit event

    Raises:
        HTTPException: If event is not found
    """
    # Find the event
    stmt = select(CreditEventTable).where(CreditEventTable.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise IntentKitAPIError(
            status_code=404, key="CreditEventNotFound", message="Credit event not found"
        )

    # Update the note
    event.note = note
    await session.commit()
    await session.refresh(event)

    return CreditEvent.model_validate(event)


async def recharge(
    session: AsyncSession,
    user_id: str,
    amount: Decimal,
    upstream_tx_id: str,
    note: Optional[str] = None,
) -> CreditAccount:
    """
    Recharge credits to a user account.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to recharge
        amount: Amount of credits to recharge
        upstream_tx_id: ID of the upstream transaction
        note: Optional note for the transaction

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount <= Decimal("0"):
        raise ValueError("Recharge amount must be positive")

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - add credits
    user_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount_details={
            CreditType.PERMANENT: amount
        },  # Recharge adds to permanent credits
        event_id=event_id,
    )

    # 3. Update platform recharge account - deduct credits
    platform_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_RECHARGE,
        credit_type=CreditType.PERMANENT,
        amount=amount,
        event_id=event_id,
    )

    # 4. Create credit event record
    event = CreditEventTable(
        id=event_id,
        event_type=EventType.RECHARGE,
        user_id=user_id,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.INCOME,
        account_id=user_account.id,
        total_amount=amount,
        credit_type=CreditType.PERMANENT,
        credit_types=[CreditType.PERMANENT],
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=amount,
        base_original_amount=amount,
        base_free_amount=Decimal("0"),  # No free credits involved in base amount
        base_reward_amount=Decimal("0"),  # No reward credits involved in base amount
        base_permanent_amount=amount,  # All base amount is permanent for recharge
        permanent_amount=amount,  # Set permanent_amount since this is a permanent credit
        free_amount=Decimal("0"),  # No free credits involved
        reward_amount=Decimal("0"),  # No reward credits involved
        agent_wallet_address=None,  # No agent involved in recharge
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (credit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECHARGE,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount,
        credit_type=CreditType.PERMANENT,
        free_amount=Decimal("0"),
        reward_amount=Decimal("0"),
        permanent_amount=amount,
    )
    session.add(user_tx)

    # 4.2 Platform recharge account transaction (debit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECHARGE,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount,
        credit_type=CreditType.PERMANENT,
        free_amount=Decimal("0"),
        reward_amount=Decimal("0"),
        permanent_amount=amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    # Send Slack notification for recharge
    try:
        send_slack_message(
            f"💰 **Credit Recharge**\n"
            f"• User ID: `{user_id}`\n"
            f"• Amount: `{amount}` credits\n"
            f"• Transaction ID: `{upstream_tx_id}`\n"
            f"• New Balance: `{user_account.credits + user_account.free_credits + user_account.reward_credits}` credits\n"
            f"• Note: {note or 'N/A'}"
        )
    except Exception as e:
        logger.error(f"Failed to send Slack notification for recharge: {str(e)}")

    return user_account


async def withdraw(
    session: AsyncSession,
    agent_id: str,
    amount: Decimal,
    upstream_tx_id: str,
    note: Optional[str] = None,
) -> CreditAccount:
    """
    Withdraw credits from an agent account to platform account.

    Args:
        session: Async session to use for database operations
        agent_id: ID of the agent to withdraw from
        amount: Amount of credits to withdraw
        upstream_tx_id: ID of the upstream transaction
        note: Optional note for the transaction

    Returns:
        Updated agent credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount <= Decimal("0"):
        raise ValueError("Withdraw amount must be positive")

    # Get agent to retrieve user_id from agent.owner
    agent = await Agent.get(agent_id)
    if not agent:
        raise IntentKitAPIError(
            status_code=404, key="AgentNotFound", message="Agent not found"
        )

    if not agent.owner:
        raise IntentKitAPIError(
            status_code=400, key="AgentNoOwner", message="Agent has no owner"
        )

    # Get agent wallet address
    agent_data = await AgentData.get(agent.id)
    agent_wallet_address = agent_data.evm_wallet_address if agent_data else None

    user_id = agent.owner

    # Get agent account to check balance
    agent_account = await CreditAccount.get_in_session(
        session=session,
        owner_type=OwnerType.AGENT,
        owner_id=agent_id,
    )

    # Check if agent has sufficient permanent credits
    if agent_account.credits < amount:
        raise IntentKitAPIError(
            status_code=400,
            key="InsufficientBalance",
            message=f"Insufficient balance. Available: {agent_account.credits}, Required: {amount}",
        )

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update agent account - deduct credits
    updated_agent_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.AGENT,
        owner_id=agent_id,
        credit_type=CreditType.PERMANENT,
        amount=amount,
        event_id=event_id,
    )

    # 3. Update platform withdraw account - add credits
    platform_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_WITHDRAW,
        amount_details={
            CreditType.PERMANENT: amount
        },  # Withdraw adds to platform permanent credits
        event_id=event_id,
    )

    # 4. Create credit event record
    event = CreditEventTable(
        id=event_id,
        event_type=EventType.WITHDRAW,
        user_id=user_id,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.EXPENSE,
        account_id=updated_agent_account.id,
        total_amount=amount,
        credit_type=CreditType.PERMANENT,
        credit_types=[CreditType.PERMANENT],
        balance_after=updated_agent_account.credits
        + updated_agent_account.free_credits
        + updated_agent_account.reward_credits,
        base_amount=amount,
        base_original_amount=amount,
        base_free_amount=Decimal("0"),  # No free credits involved in base amount
        base_reward_amount=Decimal("0"),  # No reward credits involved in base amount
        base_permanent_amount=amount,  # All base amount is permanent for withdraw
        permanent_amount=amount,  # Set permanent_amount since this is a permanent credit
        free_amount=Decimal("0"),  # No free credits involved
        reward_amount=Decimal("0"),  # No reward credits involved
        agent_wallet_address=agent_wallet_address,  # Include agent wallet address
        note=note,
    )
    session.add(event)
    await session.flush()

    # 5. Create credit transaction records
    # 5.1 Agent account transaction (debit)
    agent_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=updated_agent_account.id,
        event_id=event_id,
        tx_type=TransactionType.WITHDRAW,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount,
        credit_type=CreditType.PERMANENT,
        free_amount=Decimal("0"),
        reward_amount=Decimal("0"),
        permanent_amount=amount,
    )
    session.add(agent_tx)

    # 5.2 Platform withdraw account transaction (credit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.WITHDRAW,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount,
        credit_type=CreditType.PERMANENT,
        free_amount=Decimal("0"),
        reward_amount=Decimal("0"),
        permanent_amount=amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    # Send Slack notification for withdraw
    try:
        send_slack_message(
            f"💸 **Credit Withdraw**\n"
            f"• Agent ID: `{agent_id}`\n"
            f"• User ID: `{user_id}`\n"
            f"• Amount: `{amount}` credits\n"
            f"• Transaction ID: `{upstream_tx_id}`\n"
            f"• New Balance: `{updated_agent_account.credits}` credits\n"
            f"• Note: {note or 'N/A'}"
        )
    except Exception as e:
        logger.error(f"Failed to send Slack notification for withdraw: {str(e)}")

    return updated_agent_account


async def reward(
    session: AsyncSession,
    user_id: str,
    amount: Decimal,
    upstream_tx_id: str,
    note: Optional[str] = None,
    reward_type: Optional[RewardType] = RewardType.REWARD,
) -> CreditAccount:
    """
    Reward a user account with reward credits.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to reward
        amount: Amount of reward credits to add
        upstream_tx_id: ID of the upstream transaction
        note: Optional note for the transaction

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount <= Decimal("0"):
        raise ValueError("Reward amount must be positive")

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - add reward credits
    user_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount_details={CreditType.REWARD: amount},  # Reward adds to reward credits
        event_id=event_id,
    )

    # 3. Update platform reward account - deduct credits
    platform_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_REWARD,
        credit_type=CreditType.REWARD,
        amount=amount,
        event_id=event_id,
    )

    # 4. Create credit event record
    event = CreditEventTable(
        id=event_id,
        event_type=reward_type,
        user_id=user_id,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.INCOME,
        account_id=user_account.id,
        total_amount=amount,
        credit_type=CreditType.REWARD,
        credit_types=[CreditType.REWARD],
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=amount,
        base_original_amount=amount,
        base_free_amount=Decimal("0"),  # No free credits involved in base amount
        base_reward_amount=amount,  # All base amount is reward for reward events
        base_permanent_amount=Decimal(
            "0"
        ),  # No permanent credits involved in base amount
        reward_amount=amount,  # Set reward_amount since this is a reward credit
        free_amount=Decimal("0"),  # No free credits involved
        permanent_amount=Decimal("0"),  # No permanent credits involved
        agent_wallet_address=None,  # No agent involved in reward
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (credit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=reward_type,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount,
        credit_type=CreditType.REWARD,
        free_amount=Decimal("0"),
        reward_amount=amount,
        permanent_amount=Decimal("0"),
    )
    session.add(user_tx)

    # 4.2 Platform reward account transaction (debit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=reward_type,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount,
        credit_type=CreditType.REWARD,
        free_amount=Decimal("0"),
        reward_amount=amount,
        permanent_amount=Decimal("0"),
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    # Send Slack notification for reward
    try:
        reward_type_name = reward_type.value if reward_type else "REWARD"
        send_slack_message(
            f"🎁 **Credit Reward**\n"
            f"• User ID: `{user_id}`\n"
            f"• Amount: `{amount}` reward credits\n"
            f"• Transaction ID: `{upstream_tx_id}`\n"
            f"• Reward Type: `{reward_type_name}`\n"
            f"• New Balance: `{user_account.credits + user_account.free_credits + user_account.reward_credits}` credits\n"
            f"• Note: {note or 'N/A'}"
        )
    except Exception as e:
        logger.error(f"Failed to send Slack notification for reward: {str(e)}")

    return user_account


async def adjustment(
    session: AsyncSession,
    user_id: str,
    credit_type: CreditType,
    amount: Decimal,
    upstream_tx_id: str,
    note: str,
) -> CreditAccount:
    """
    Adjust a user account's credits (can be positive or negative).

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to adjust
        credit_type: Type of credit to adjust (FREE, REWARD, or PERMANENT)
        amount: Amount to adjust (positive for increase, negative for decrease)
        upstream_tx_id: ID of the upstream transaction
        note: Required explanation for the adjustment

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount == Decimal("0"):
        raise ValueError("Adjustment amount cannot be zero")

    if not note:
        raise ValueError("Adjustment requires a note explaining the reason")

    # Determine direction based on amount sign
    is_income = amount > Decimal("0")
    abs_amount = abs(amount)
    direction = Direction.INCOME if is_income else Direction.EXPENSE
    credit_debit_user = CreditDebit.CREDIT if is_income else CreditDebit.DEBIT
    credit_debit_platform = CreditDebit.DEBIT if is_income else CreditDebit.CREDIT

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account
    if is_income:
        user_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.USER,
            owner_id=user_id,
            amount_details={credit_type: abs_amount},
            event_id=event_id,
        )
    else:
        # Deduct the credits using deduction_in_session
        # For adjustment, we don't check if the user has enough credits
        # It can be positive or negative
        user_account = await CreditAccount.deduction_in_session(
            session=session,
            owner_type=OwnerType.USER,
            owner_id=user_id,
            credit_type=credit_type,
            amount=abs_amount,
            event_id=event_id,
        )

    # 3. Update platform adjustment account
    if is_income:
        platform_account = await CreditAccount.deduction_in_session(
            session=session,
            owner_type=OwnerType.PLATFORM,
            owner_id=DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
            credit_type=credit_type,
            amount=abs_amount,
            event_id=event_id,
        )
    else:
        platform_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.PLATFORM,
            owner_id=DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
            amount_details={credit_type: abs_amount},
            event_id=event_id,
        )

    # 4. Create credit event record
    # Set the appropriate credit amount field based on credit type
    free_amount = Decimal("0")
    reward_amount = Decimal("0")
    permanent_amount = Decimal("0")

    if credit_type == CreditType.FREE:
        free_amount = abs_amount
    elif credit_type == CreditType.REWARD:
        reward_amount = abs_amount
    elif credit_type == CreditType.PERMANENT:
        permanent_amount = abs_amount

    event = CreditEventTable(
        id=event_id,
        event_type=EventType.ADJUSTMENT,
        user_id=user_id,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=direction,
        account_id=user_account.id,
        total_amount=abs_amount,
        credit_type=credit_type,
        credit_types=[credit_type],
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=abs_amount,
        base_original_amount=abs_amount,
        base_free_amount=free_amount,
        base_reward_amount=reward_amount,
        base_permanent_amount=permanent_amount,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
        agent_wallet_address=None,  # No agent involved in adjustment
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.ADJUSTMENT,
        credit_debit=credit_debit_user,
        change_amount=abs_amount,
        credit_type=credit_type,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
    )
    session.add(user_tx)

    # 4.2 Platform adjustment account transaction
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.ADJUSTMENT,
        credit_debit=credit_debit_platform,
        change_amount=abs_amount,
        credit_type=credit_type,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    return user_account


async def update_daily_quota(
    session: AsyncSession,
    user_id: str,
    free_quota: Optional[Decimal] = None,
    refill_amount: Optional[Decimal] = None,
    upstream_tx_id: str = "",
    note: str = "",
) -> CreditAccount:
    """
    Update the daily quota and refill amount of a user's credit account.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to update
        free_quota: Optional new daily quota value
        refill_amount: Optional amount to refill hourly, not exceeding free_quota
        upstream_tx_id: ID of the upstream transaction (for logging purposes)
        note: Explanation for changing the daily quota

    Returns:
        Updated user credit account
    """
    return await CreditAccount.update_daily_quota(
        session, user_id, free_quota, refill_amount, upstream_tx_id, note
    )


async def list_credit_events_by_user(
    session: AsyncSession,
    user_id: str,
    direction: Optional[Direction] = None,
    cursor: Optional[str] = None,
    limit: int = 20,
    event_type: Optional[EventType] = None,
) -> Tuple[List[CreditEvent], Optional[str], bool]:
    """
    List credit events for a user account with cursor pagination.

    Args:
        session: Async database session.
        user_id: The ID of the user.
        direction: The direction of the events (INCOME or EXPENSE).
        cursor: The ID of the last event from the previous page.
        limit: Maximum number of events to return per page.
        event_type: Optional filter for specific event type.

    Returns:
        A tuple containing:
        - A list of CreditEvent models.
        - The cursor for the next page (ID of the last event in the list).
        - A boolean indicating if there are more events available.
    """
    # 1. Find the account for the owner
    account = await CreditAccount.get_in_session(session, OwnerType.USER, user_id)
    if not account:
        # Decide if returning empty or raising error is better. Empty list seems reasonable.
        # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{owner_type.value.capitalize()} account not found")
        return [], None, False

    # 2. Build the query
    stmt = (
        select(CreditEventTable)
        .where(CreditEventTable.account_id == account.id)
        .order_by(desc(CreditEventTable.id))
        .limit(limit + 1)  # Fetch one extra to check if there are more
    )

    # 3. Apply optional filter if provided
    if direction:
        stmt = stmt.where(CreditEventTable.direction == direction.value)
    if event_type:
        stmt = stmt.where(CreditEventTable.event_type == event_type.value)

    # 4. Apply cursor filter if provided
    if cursor:
        stmt = stmt.where(CreditEventTable.id < cursor)

    # 5. Execute query
    result = await session.execute(stmt)
    events_data = result.scalars().all()

    # 6. Determine pagination details
    has_more = len(events_data) > limit
    events_to_return = events_data[:limit]  # Slice to the requested limit

    next_cursor = events_to_return[-1].id if events_to_return and has_more else None

    # 7. Convert to Pydantic models
    events_models = [CreditEvent.model_validate(event) for event in events_to_return]

    return events_models, next_cursor, has_more


async def list_credit_events(
    session: AsyncSession,
    direction: Optional[Direction] = Direction.EXPENSE,
    cursor: Optional[str] = None,
    limit: int = 20,
    event_type: Optional[EventType] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
) -> Tuple[List[CreditEvent], Optional[str], bool]:
    """
    List all credit events with cursor pagination.

    Args:
        session: Async database session.
        direction: The direction of the events (INCOME or EXPENSE). Default is EXPENSE.
        cursor: The ID of the last event from the previous page.
        limit: Maximum number of events to return per page.
        event_type: Optional filter for specific event type.
        start_at: Optional start datetime to filter events by created_at.
        end_at: Optional end datetime to filter events by created_at.

    Returns:
        A tuple containing:
        - A list of CreditEvent models.
        - The cursor for the next page (ID of the last event in the list).
        - A boolean indicating if there are more events available.
    """
    # Build the query
    stmt = (
        select(CreditEventTable)
        .order_by(CreditEventTable.id)  # Ascending order as required
        .limit(limit + 1)  # Fetch one extra to check if there are more
    )

    # Apply direction filter (default is EXPENSE)
    if direction:
        stmt = stmt.where(CreditEventTable.direction == direction.value)

    # Apply optional event_type filter if provided
    if event_type:
        stmt = stmt.where(CreditEventTable.event_type == event_type.value)

    # Apply datetime filters if provided
    if start_at:
        stmt = stmt.where(CreditEventTable.created_at >= start_at)
    if end_at:
        stmt = stmt.where(CreditEventTable.created_at < end_at)

    # Apply cursor filter if provided
    if cursor:
        stmt = stmt.where(CreditEventTable.id > cursor)  # Using > for ascending order

    # Execute query
    result = await session.execute(stmt)
    events_data = result.scalars().all()

    # Determine pagination details
    has_more = len(events_data) > limit
    events_to_return = events_data[:limit]  # Slice to the requested limit

    # always return a cursor even there is no next page
    next_cursor = events_to_return[-1].id if events_to_return else None

    # Convert to Pydantic models
    events_models = [CreditEvent.model_validate(event) for event in events_to_return]

    return events_models, next_cursor, has_more


async def list_fee_events_by_agent(
    session: AsyncSession,
    agent_id: str,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> Tuple[List[CreditEvent], Optional[str], bool]:
    """
    List fee events for an agent with cursor pagination.
    These events represent income for the agent from users' expenses.

    Args:
        session: Async database session.
        agent_id: The ID of the agent.
        cursor: The ID of the last event from the previous page.
        limit: Maximum number of events to return per page.

    Returns:
        A tuple containing:
        - A list of CreditEvent models.
        - The cursor for the next page (ID of the last event in the list).
        - A boolean indicating if there are more events available.
    """
    # 1. Find the account for the agent
    agent_account = await CreditAccount.get_in_session(
        session, OwnerType.AGENT, agent_id
    )
    if not agent_account:
        return [], None, False

    # 2. Build the query to find events where fee_agent_amount > 0 and fee_agent_account = agent_account.id
    stmt = (
        select(CreditEventTable)
        .where(CreditEventTable.fee_agent_account == agent_account.id)
        .where(CreditEventTable.fee_agent_amount > 0)
        .order_by(desc(CreditEventTable.id))
        .limit(limit + 1)  # Fetch one extra to check if there are more
    )

    # 3. Apply cursor filter if provided
    if cursor:
        stmt = stmt.where(CreditEventTable.id < cursor)

    # 4. Execute query
    result = await session.execute(stmt)
    events_data = result.scalars().all()

    # 5. Determine pagination details
    has_more = len(events_data) > limit
    events_to_return = events_data[:limit]  # Slice to the requested limit

    next_cursor = events_to_return[-1].id if events_to_return and has_more else None

    # 6. Convert to Pydantic models
    events_models = [CreditEvent.model_validate(event) for event in events_to_return]

    return events_models, next_cursor, has_more


async def fetch_credit_event_by_upstream_tx_id(
    session: AsyncSession,
    upstream_tx_id: str,
) -> CreditEvent:
    """
    Fetch a credit event by its upstream transaction ID.

    Args:
        session: Async database session.
        upstream_tx_id: ID of the upstream transaction.

    Returns:
        The credit event if found.

    Raises:
        HTTPException: If the credit event is not found.
    """
    # Build the query to find the event by upstream_tx_id
    stmt = select(CreditEventTable).where(
        CreditEventTable.upstream_tx_id == upstream_tx_id
    )

    # Execute query
    result = await session.scalar(stmt)

    # Raise 404 if not found
    if not result:
        raise IntentKitAPIError(
            status_code=404,
            key="CreditEventNotFound",
            message=f"Credit event with upstream_tx_id '{upstream_tx_id}' not found",
        )

    # Convert to Pydantic model and return
    return CreditEvent.model_validate(result)


async def fetch_credit_event_by_id(
    session: AsyncSession,
    event_id: str,
) -> CreditEvent:
    """
    Fetch a credit event by its ID.

    Args:
        session: Async database session.
        event_id: ID of the credit event.

    Returns:
        The credit event if found.

    Raises:
        IntentKitAPIError: If the credit event is not found.
    """
    # Build the query to find the event by ID
    stmt = select(CreditEventTable).where(CreditEventTable.id == event_id)

    # Execute query
    result = await session.scalar(stmt)

    # Raise 404 if not found
    if not result:
        raise IntentKitAPIError(
            status_code=404,
            key="CreditEventNotFound",
            message=f"Credit event with ID '{event_id}' not found",
        )

    # Convert to Pydantic model and return
    return CreditEvent.model_validate(result)


async def expense_message(
    session: AsyncSession,
    user_id: str,
    message_id: str,
    start_message_id: str,
    base_llm_amount: Decimal,
    agent: Agent,
) -> CreditEvent:
    """
    Deduct credits from a user account for message expenses.
    Don't forget to commit the session after calling this function.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to deduct credits from
        message_id: ID of the message that incurred the expense
        start_message_id: ID of the starting message in a conversation
        base_llm_amount: Amount of LLM costs

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.EXECUTOR, message_id
    )

    # Ensure base_llm_amount has 4 decimal places
    base_llm_amount = base_llm_amount.quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    if base_llm_amount < Decimal("0"):
        raise ValueError("Base LLM amount must be non-negative")

    # Get payment settings
    payment_settings = await AppSetting.payment()

    # Calculate amount with exact 4 decimal places
    base_original_amount = base_llm_amount
    base_amount = base_original_amount
    fee_platform_amount = (
        base_amount * payment_settings.fee_platform_percentage / Decimal("100")
    ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    fee_agent_amount = Decimal("0")
    if agent.fee_percentage and user_id != agent.owner:
        fee_agent_amount = (
            (base_amount + fee_platform_amount) * agent.fee_percentage / Decimal("100")
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    total_amount = (base_amount + fee_platform_amount + fee_agent_amount).quantize(
        FOURPLACES, rounding=ROUND_HALF_UP
    )

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - deduct credits
    user_account, details = await CreditAccount.expense_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount=total_amount,
        event_id=event_id,
    )

    # If using free credits, add to agent's free_income_daily
    if details.get(CreditType.FREE):
        from intentkit.models.agent_data import AgentQuota

        await AgentQuota.add_free_income_in_session(
            session=session, id=agent.id, amount=details.get(CreditType.FREE)
        )

    # 3. Calculate detailed amounts for fees based on user payment details
    # Set the appropriate credit amount field based on credit type
    free_amount = details.get(CreditType.FREE, Decimal("0"))
    reward_amount = details.get(CreditType.REWARD, Decimal("0"))
    permanent_amount = details.get(CreditType.PERMANENT, Decimal("0"))
    if CreditType.PERMANENT in details:
        credit_type = CreditType.PERMANENT
    elif CreditType.REWARD in details:
        credit_type = CreditType.REWARD
    else:
        credit_type = CreditType.FREE

    # Calculate fee_platform amounts by credit type
    fee_platform_free_amount = Decimal("0")
    fee_platform_reward_amount = Decimal("0")
    fee_platform_permanent_amount = Decimal("0")

    if fee_platform_amount > Decimal("0") and total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_platform_free_amount = (
                free_amount * fee_platform_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_platform_reward_amount = (
                reward_amount * fee_platform_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_platform_amount
        fee_platform_permanent_amount = (
            fee_platform_amount - fee_platform_free_amount - fee_platform_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate fee_agent amounts by credit type
    fee_agent_free_amount = Decimal("0")
    fee_agent_reward_amount = Decimal("0")
    fee_agent_permanent_amount = Decimal("0")

    if fee_agent_amount > Decimal("0") and total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_agent_free_amount = (
                free_amount * fee_agent_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_agent_reward_amount = (
                reward_amount * fee_agent_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_agent_amount
        fee_agent_permanent_amount = (
            fee_agent_amount - fee_agent_free_amount - fee_agent_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate base amounts by credit type using subtraction method
    # This ensures that: permanent_amount = base_permanent_amount + fee_platform_permanent_amount + fee_agent_permanent_amount
    base_free_amount = free_amount - fee_platform_free_amount - fee_agent_free_amount
    base_reward_amount = (
        reward_amount - fee_platform_reward_amount - fee_agent_reward_amount
    )
    base_permanent_amount = (
        permanent_amount - fee_platform_permanent_amount - fee_agent_permanent_amount
    )

    # 4. Update fee account - add credits with detailed amounts
    message_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_MESSAGE,
        amount_details={
            CreditType.FREE: base_free_amount,
            CreditType.REWARD: base_reward_amount,
            CreditType.PERMANENT: base_permanent_amount,
        },
        event_id=event_id,
    )
    platform_fee_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_FEE,
        amount_details={
            CreditType.FREE: fee_platform_free_amount,
            CreditType.REWARD: fee_platform_reward_amount,
            CreditType.PERMANENT: fee_platform_permanent_amount,
        },
        event_id=event_id,
    )
    if fee_agent_amount > 0:
        agent_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.AGENT,
            owner_id=agent.id,
            amount_details={
                CreditType.FREE: fee_agent_free_amount,
                CreditType.REWARD: fee_agent_reward_amount,
                CreditType.PERMANENT: fee_agent_permanent_amount,
            },
            event_id=event_id,
        )

    # Get agent wallet address
    agent_data = await AgentData.get(agent.id)
    agent_wallet_address = agent_data.evm_wallet_address if agent_data else None

    event = CreditEventTable(
        id=event_id,
        account_id=user_account.id,
        event_type=EventType.MESSAGE,
        user_id=user_id,
        upstream_type=UpstreamType.EXECUTOR,
        upstream_tx_id=message_id,
        direction=Direction.EXPENSE,
        agent_id=agent.id,
        message_id=message_id,
        start_message_id=start_message_id,
        model=agent.model,
        total_amount=total_amount,
        credit_type=credit_type,
        credit_types=list(details.keys()),
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=base_amount,
        base_original_amount=base_original_amount,
        base_free_amount=base_free_amount,
        base_reward_amount=base_reward_amount,
        base_permanent_amount=base_permanent_amount,
        base_llm_amount=base_llm_amount,
        fee_platform_amount=fee_platform_amount,
        fee_platform_free_amount=fee_platform_free_amount,
        fee_platform_reward_amount=fee_platform_reward_amount,
        fee_platform_permanent_amount=fee_platform_permanent_amount,
        fee_agent_amount=fee_agent_amount,
        fee_agent_account=agent_account.id if fee_agent_amount > 0 else None,
        fee_agent_free_amount=fee_agent_free_amount,
        fee_agent_reward_amount=fee_agent_reward_amount,
        fee_agent_permanent_amount=fee_agent_permanent_amount,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
        agent_wallet_address=agent_wallet_address,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (debit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.PAY,
        credit_debit=CreditDebit.DEBIT,
        change_amount=total_amount,
        credit_type=credit_type,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
    )
    session.add(user_tx)

    # 4.2 Message account transaction (credit)
    message_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=message_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_BASE_LLM,
        credit_debit=CreditDebit.CREDIT,
        change_amount=base_amount,
        credit_type=credit_type,
        free_amount=base_free_amount,
        reward_amount=base_reward_amount,
        permanent_amount=base_permanent_amount,
    )
    session.add(message_tx)

    # 4.3 Platform fee account transaction (credit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_fee_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_FEE_PLATFORM,
        credit_debit=CreditDebit.CREDIT,
        change_amount=fee_platform_amount,
        credit_type=credit_type,
        free_amount=fee_platform_free_amount,
        reward_amount=fee_platform_reward_amount,
        permanent_amount=fee_platform_permanent_amount,
    )
    session.add(platform_tx)

    # 4.4 Agent fee account transaction (credit)
    if fee_agent_amount > 0:
        agent_tx = CreditTransactionTable(
            id=str(XID()),
            account_id=agent_account.id,
            event_id=event_id,
            tx_type=TransactionType.RECEIVE_FEE_AGENT,
            credit_debit=CreditDebit.CREDIT,
            change_amount=fee_agent_amount,
            credit_type=credit_type,
            free_amount=fee_agent_free_amount,
            reward_amount=fee_agent_reward_amount,
            permanent_amount=fee_agent_permanent_amount,
        )
        session.add(agent_tx)

    await session.refresh(event)

    return CreditEvent.model_validate(event)


class SkillCost(BaseModel):
    total_amount: Decimal
    base_amount: Decimal
    base_discount_amount: Decimal
    base_original_amount: Decimal
    base_skill_amount: Decimal
    fee_platform_amount: Decimal
    fee_dev_user: str
    fee_dev_user_type: OwnerType
    fee_dev_amount: Decimal
    fee_agent_amount: Decimal


async def skill_cost(
    skill_name: str,
    user_id: str,
    agent: Agent,
) -> SkillCost:
    """
    Calculate the cost for a skill call including all fees.

    Args:
        skill_name: Name of the skill
        user_id: ID of the user making the skill call
        agent: Agent using the skill

    Returns:
        SkillCost: Object containing all cost components
    """

    skill = await Skill.get(skill_name)
    if not skill:
        raise ValueError(f"The price of {skill_name} not set yet")
    agent_skill_config = agent.skills.get(skill.category)
    if (
        agent_skill_config
        and agent_skill_config.get("api_key_provider") == "agent_owner"
    ):
        base_skill_amount = skill.price_self_key.quantize(
            FOURPLACES, rounding=ROUND_HALF_UP
        )
    else:
        base_skill_amount = skill.price.quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    # Get payment settings
    payment_settings = await AppSetting.payment()

    # Calculate fee
    if skill.author:
        fee_dev_user = skill.author
        fee_dev_user_type = OwnerType.USER
    else:
        fee_dev_user = DEFAULT_PLATFORM_ACCOUNT_DEV
        fee_dev_user_type = OwnerType.PLATFORM
    fee_dev_percentage = payment_settings.fee_dev_percentage

    if base_skill_amount < Decimal("0"):
        raise ValueError("Base skill amount must be non-negative")

    # Calculate amount with exact 4 decimal places
    base_original_amount = base_skill_amount
    base_amount = base_original_amount
    fee_platform_amount = (
        base_amount * payment_settings.fee_platform_percentage / Decimal("100")
    ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    fee_dev_amount = (base_amount * fee_dev_percentage / Decimal("100")).quantize(
        FOURPLACES, rounding=ROUND_HALF_UP
    )
    fee_agent_amount = Decimal("0")
    if agent.fee_percentage and user_id != agent.owner:
        fee_agent_amount = (
            (base_amount + fee_platform_amount + fee_dev_amount)
            * agent.fee_percentage
            / Decimal("100")
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    total_amount = (
        base_amount + fee_platform_amount + fee_dev_amount + fee_agent_amount
    ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Return the SkillCost object with all calculated values
    return SkillCost(
        total_amount=total_amount,
        base_amount=base_amount,
        base_discount_amount=Decimal("0"),  # No discount in this implementation
        base_original_amount=base_original_amount,
        base_skill_amount=base_skill_amount,
        fee_platform_amount=fee_platform_amount,
        fee_dev_user=fee_dev_user,
        fee_dev_user_type=fee_dev_user_type,
        fee_dev_amount=fee_dev_amount,
        fee_agent_amount=fee_agent_amount,
    )


async def expense_skill(
    session: AsyncSession,
    user_id: str,
    message_id: str,
    start_message_id: str,
    skill_call_id: str,
    skill_name: str,
    agent: Agent,
) -> CreditEvent:
    """
    Deduct credits from a user account for message expenses.
    Don't forget to commit the session after calling this function.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to deduct credits from
        message_id: ID of the message that incurred the expense
        start_message_id: ID of the starting message in a conversation
        skill_call_id: ID of the skill call
        skill_name: Name of the skill being used
        agent: Agent using the skill

    Returns:
        CreditEvent: The created credit event
    """
    # Check for idempotency - prevent duplicate transactions
    upstream_tx_id = f"{message_id}_{skill_call_id}"
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.EXECUTOR, upstream_tx_id
    )
    logger.info(f"[{agent.id}] skill payment {skill_name}")

    # Calculate skill cost using the skill_cost function
    skill_cost_info = await skill_cost(skill_name, user_id, agent)

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - deduct credits
    user_account, details = await CreditAccount.expense_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount=skill_cost_info.total_amount,
        event_id=event_id,
    )

    # If using free credits, add to agent's free_income_daily
    if CreditType.FREE in details:
        from intentkit.models.agent_data import AgentQuota

        await AgentQuota.add_free_income_in_session(
            session=session, id=agent.id, amount=details[CreditType.FREE]
        )

    # 3. Calculate detailed amounts for fees
    # Set the appropriate credit amount field based on credit type
    free_amount = details.get(CreditType.FREE, Decimal("0"))
    reward_amount = details.get(CreditType.REWARD, Decimal("0"))
    permanent_amount = details.get(CreditType.PERMANENT, Decimal("0"))
    if CreditType.PERMANENT in details:
        credit_type = CreditType.PERMANENT
    elif CreditType.REWARD in details:
        credit_type = CreditType.REWARD
    else:
        credit_type = CreditType.FREE

    # Calculate fee_platform amounts by credit type
    fee_platform_free_amount = Decimal("0")
    fee_platform_reward_amount = Decimal("0")
    fee_platform_permanent_amount = Decimal("0")

    if skill_cost_info.fee_platform_amount > Decimal(
        "0"
    ) and skill_cost_info.total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_platform_free_amount = (
                free_amount
                * skill_cost_info.fee_platform_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_platform_reward_amount = (
                reward_amount
                * skill_cost_info.fee_platform_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_platform_amount
        fee_platform_permanent_amount = (
            skill_cost_info.fee_platform_amount
            - fee_platform_free_amount
            - fee_platform_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate fee_agent amounts by credit type
    fee_agent_free_amount = Decimal("0")
    fee_agent_reward_amount = Decimal("0")
    fee_agent_permanent_amount = Decimal("0")

    if skill_cost_info.fee_agent_amount > Decimal(
        "0"
    ) and skill_cost_info.total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_agent_free_amount = (
                free_amount
                * skill_cost_info.fee_agent_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_agent_reward_amount = (
                reward_amount
                * skill_cost_info.fee_agent_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_agent_amount
        fee_agent_permanent_amount = (
            skill_cost_info.fee_agent_amount
            - fee_agent_free_amount
            - fee_agent_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate fee_dev amounts by credit type
    fee_dev_free_amount = Decimal("0")
    fee_dev_reward_amount = Decimal("0")
    fee_dev_permanent_amount = Decimal("0")

    if skill_cost_info.fee_dev_amount > Decimal(
        "0"
    ) and skill_cost_info.total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_dev_free_amount = (
                free_amount
                * skill_cost_info.fee_dev_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_dev_reward_amount = (
                reward_amount
                * skill_cost_info.fee_dev_amount
                / skill_cost_info.total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_dev_amount
        fee_dev_permanent_amount = (
            skill_cost_info.fee_dev_amount - fee_dev_free_amount - fee_dev_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate base amounts by credit type using subtraction method
    base_free_amount = (
        free_amount
        - fee_platform_free_amount
        - fee_agent_free_amount
        - fee_dev_free_amount
    )

    base_reward_amount = (
        reward_amount
        - fee_platform_reward_amount
        - fee_agent_reward_amount
        - fee_dev_reward_amount
    )

    base_permanent_amount = (
        permanent_amount
        - fee_platform_permanent_amount
        - fee_agent_permanent_amount
        - fee_dev_permanent_amount
    )

    # 4. Update fee account - add credits
    skill_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_SKILL,
        amount_details={
            CreditType.FREE: base_free_amount,
            CreditType.REWARD: base_reward_amount,
            CreditType.PERMANENT: base_permanent_amount,
        },
        event_id=event_id,
    )
    platform_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_FEE,
        amount_details={
            CreditType.FREE: fee_platform_free_amount,
            CreditType.REWARD: fee_platform_reward_amount,
            CreditType.PERMANENT: fee_platform_permanent_amount,
        },
        event_id=event_id,
    )
    if skill_cost_info.fee_dev_amount > 0:
        dev_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=skill_cost_info.fee_dev_user_type,
            owner_id=skill_cost_info.fee_dev_user,
            amount_details={
                CreditType.FREE: fee_dev_free_amount,
                CreditType.REWARD: fee_dev_reward_amount,
                CreditType.PERMANENT: fee_dev_permanent_amount,
            },
            event_id=event_id,
        )
    if skill_cost_info.fee_agent_amount > 0:
        agent_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.AGENT,
            owner_id=agent.id,
            amount_details={
                CreditType.FREE: fee_agent_free_amount,
                CreditType.REWARD: fee_agent_reward_amount,
                CreditType.PERMANENT: fee_agent_permanent_amount,
            },
            event_id=event_id,
        )

    # 5. Create credit event record

    # Get agent wallet address
    agent_data = await AgentData.get(agent.id)
    agent_wallet_address = agent_data.evm_wallet_address if agent_data else None

    event = CreditEventTable(
        id=event_id,
        account_id=user_account.id,
        event_type=EventType.SKILL_CALL,
        user_id=user_id,
        upstream_type=UpstreamType.EXECUTOR,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.EXPENSE,
        agent_id=agent.id,
        message_id=message_id,
        start_message_id=start_message_id,
        skill_call_id=skill_call_id,
        skill_name=skill_name,
        total_amount=skill_cost_info.total_amount,
        credit_type=credit_type,
        credit_types=details.keys(),
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=skill_cost_info.base_amount,
        base_original_amount=skill_cost_info.base_original_amount,
        base_skill_amount=skill_cost_info.base_skill_amount,
        base_free_amount=base_free_amount,
        base_reward_amount=base_reward_amount,
        base_permanent_amount=base_permanent_amount,
        fee_platform_amount=skill_cost_info.fee_platform_amount,
        fee_platform_free_amount=fee_platform_free_amount,
        fee_platform_reward_amount=fee_platform_reward_amount,
        fee_platform_permanent_amount=fee_platform_permanent_amount,
        fee_agent_amount=skill_cost_info.fee_agent_amount,
        fee_agent_account=agent_account.id
        if skill_cost_info.fee_agent_amount > 0
        else None,
        fee_agent_free_amount=fee_agent_free_amount,
        fee_agent_reward_amount=fee_agent_reward_amount,
        fee_agent_permanent_amount=fee_agent_permanent_amount,
        fee_dev_amount=skill_cost_info.fee_dev_amount,
        fee_dev_account=dev_account.id if skill_cost_info.fee_dev_amount > 0 else None,
        fee_dev_free_amount=fee_dev_free_amount,
        fee_dev_reward_amount=fee_dev_reward_amount,
        fee_dev_permanent_amount=fee_dev_permanent_amount,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
        agent_wallet_address=agent_wallet_address,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (debit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.PAY,
        credit_debit=CreditDebit.DEBIT,
        change_amount=skill_cost_info.total_amount,
        credit_type=credit_type,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
    )
    session.add(user_tx)

    # 4.2 Skill account transaction (credit)
    skill_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=skill_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_BASE_SKILL,
        credit_debit=CreditDebit.CREDIT,
        change_amount=skill_cost_info.base_amount,
        credit_type=credit_type,
        free_amount=base_free_amount,
        reward_amount=base_reward_amount,
        permanent_amount=base_permanent_amount,
    )
    session.add(skill_tx)

    # 4.3 Platform fee account transaction (credit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_FEE_PLATFORM,
        credit_debit=CreditDebit.CREDIT,
        change_amount=skill_cost_info.fee_platform_amount,
        credit_type=credit_type,
        free_amount=fee_platform_free_amount,
        reward_amount=fee_platform_reward_amount,
        permanent_amount=fee_platform_permanent_amount,
    )
    session.add(platform_tx)

    # 4.4 Dev user transaction (credit)
    if skill_cost_info.fee_dev_amount > 0:
        dev_tx = CreditTransactionTable(
            id=str(XID()),
            account_id=dev_account.id,
            event_id=event_id,
            tx_type=TransactionType.RECEIVE_FEE_DEV,
            credit_debit=CreditDebit.CREDIT,
            change_amount=skill_cost_info.fee_dev_amount,
            credit_type=CreditType.REWARD,
            free_amount=fee_dev_free_amount,
            reward_amount=fee_dev_reward_amount,
            permanent_amount=fee_dev_permanent_amount,
        )
        session.add(dev_tx)

    # 4.5 Agent fee account transaction (credit)
    if skill_cost_info.fee_agent_amount > 0:
        agent_tx = CreditTransactionTable(
            id=str(XID()),
            account_id=agent_account.id,
            event_id=event_id,
            tx_type=TransactionType.RECEIVE_FEE_AGENT,
            credit_debit=CreditDebit.CREDIT,
            change_amount=skill_cost_info.fee_agent_amount,
            credit_type=credit_type,
            free_amount=fee_agent_free_amount,
            reward_amount=fee_agent_reward_amount,
            permanent_amount=fee_agent_permanent_amount,
        )
        session.add(agent_tx)

    # Commit all changes
    await session.refresh(event)

    return CreditEvent.model_validate(event)


async def refill_free_credits_for_account(
    session: AsyncSession,
    account: CreditAccount,
):
    """
    Refill free credits for a single account based on its refill_amount and free_quota.

    Args:
        session: Async session to use for database operations
        account: The credit account to refill
    """
    # Skip if refill_amount is zero or free_credits already equals or exceeds free_quota
    if (
        account.refill_amount <= Decimal("0")
        or account.free_credits >= account.free_quota
    ):
        return

    # Calculate the amount to add
    # If adding refill_amount would exceed free_quota, only add what's needed to reach free_quota
    amount_to_add = min(
        account.refill_amount, account.free_quota - account.free_credits
    ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    if amount_to_add <= Decimal("0"):
        return  # Nothing to add

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - add free credits
    updated_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=account.owner_type,
        owner_id=account.owner_id,
        amount_details={CreditType.FREE: amount_to_add},
        event_id=event_id,
    )

    # 3. Update platform refill account - deduct credits
    platform_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_REFILL,
        credit_type=CreditType.FREE,
        amount=amount_to_add,
        event_id=event_id,
    )

    # 4. Create credit event record
    event = CreditEventTable(
        id=event_id,
        account_id=updated_account.id,
        event_type=EventType.REFILL,
        user_id=account.owner_id,
        upstream_type=UpstreamType.SCHEDULER,
        upstream_tx_id=str(XID()),
        direction=Direction.INCOME,
        credit_type=CreditType.FREE,
        credit_types=[CreditType.FREE],
        total_amount=amount_to_add,
        balance_after=updated_account.credits
        + updated_account.free_credits
        + updated_account.reward_credits,
        base_amount=amount_to_add,
        base_original_amount=amount_to_add,
        base_free_amount=amount_to_add,
        base_reward_amount=Decimal("0"),
        base_permanent_amount=Decimal("0"),
        free_amount=amount_to_add,  # Set free_amount since this is a free credit refill
        reward_amount=Decimal("0"),  # No reward credits involved
        permanent_amount=Decimal("0"),  # No permanent credits involved
        agent_wallet_address=None,  # No agent involved in refill
        note=f"Hourly free credits refill of {amount_to_add}",
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (credit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=updated_account.id,
        event_id=event_id,
        tx_type=TransactionType.REFILL,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount_to_add,
        credit_type=CreditType.FREE,
        free_amount=amount_to_add,
        reward_amount=Decimal("0"),
        permanent_amount=Decimal("0"),
    )
    session.add(user_tx)

    # 4.2 Platform refill account transaction (debit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.REFILL,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount_to_add,
        credit_type=CreditType.FREE,
        free_amount=amount_to_add,
        reward_amount=Decimal("0"),
        permanent_amount=Decimal("0"),
    )
    session.add(platform_tx)

    # Commit changes
    await session.commit()
    logger.info(
        f"Refilled {amount_to_add} free credits for account {account.owner_type} {account.owner_id}"
    )


async def refill_all_free_credits():
    """
    Find all eligible accounts and refill their free credits.
    Eligible accounts are those with refill_amount > 0 and free_credits < free_quota.
    """
    async with get_session() as session:
        # Find all accounts that need refilling
        stmt = select(CreditAccountTable).where(
            CreditAccountTable.refill_amount > 0,
            CreditAccountTable.free_credits < CreditAccountTable.free_quota,
        )
        result = await session.execute(stmt)
        accounts_data = result.scalars().all()

        # Convert to Pydantic models
        accounts = [CreditAccount.model_validate(account) for account in accounts_data]

    # Process each account
    refilled_count = 0
    for account in accounts:
        async with get_session() as session:
            try:
                await refill_free_credits_for_account(session, account)
                refilled_count += 1
            except Exception as e:
                logger.error(f"Error refilling account {account.id}: {str(e)}")
            # Continue with other accounts even if one fails
            continue
    logger.info(f"Refilled {refilled_count} accounts")


async def expense_summarize(
    session: AsyncSession,
    user_id: str,
    message_id: str,
    start_message_id: str,
    base_llm_amount: Decimal,
    agent: Agent,
) -> CreditEvent:
    """
    Deduct credits from a user account for memory/summarize expenses.
    Don't forget to commit the session after calling this function.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to deduct credits from
        message_id: ID of the message that incurred the expense
        start_message_id: ID of the starting message in a conversation
        base_llm_amount: Amount of LLM costs
        agent: Agent instance

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.EXECUTOR, message_id
    )

    # Ensure base_llm_amount has 4 decimal places
    base_llm_amount = base_llm_amount.quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    if base_llm_amount < Decimal("0"):
        raise ValueError("Base LLM amount must be non-negative")

    # Get payment settings
    payment_settings = await AppSetting.payment()

    # Calculate amount with exact 4 decimal places
    base_original_amount = base_llm_amount
    base_amount = base_original_amount
    fee_platform_amount = (
        base_amount * payment_settings.fee_platform_percentage / Decimal("100")
    ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    fee_agent_amount = Decimal("0")
    if agent.fee_percentage and user_id != agent.owner:
        fee_agent_amount = (
            (base_amount + fee_platform_amount) * agent.fee_percentage / Decimal("100")
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
    total_amount = (base_amount + fee_platform_amount + fee_agent_amount).quantize(
        FOURPLACES, rounding=ROUND_HALF_UP
    )

    # 1. Create credit event record first to get event_id
    event_id = str(XID())

    # 2. Update user account - deduct credits
    user_account, details = await CreditAccount.expense_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount=total_amount,
        event_id=event_id,
    )

    # If using free credits, add to agent's free_income_daily
    if details.get(CreditType.FREE):
        from intentkit.models.agent_data import AgentQuota

        await AgentQuota.add_free_income_in_session(
            session=session, id=agent.id, amount=details.get(CreditType.FREE)
        )

    # 3. Calculate fee amounts by credit type before income_in_session calls
    # Set the appropriate credit amount field based on credit type
    free_amount = details.get(CreditType.FREE, Decimal("0"))
    reward_amount = details.get(CreditType.REWARD, Decimal("0"))
    permanent_amount = details.get(CreditType.PERMANENT, Decimal("0"))

    if CreditType.PERMANENT in details:
        credit_type = CreditType.PERMANENT
    elif CreditType.REWARD in details:
        credit_type = CreditType.REWARD
    else:
        credit_type = CreditType.FREE

    # Calculate fee_platform amounts by credit type
    fee_platform_free_amount = Decimal("0")
    fee_platform_reward_amount = Decimal("0")
    fee_platform_permanent_amount = Decimal("0")

    if fee_platform_amount > Decimal("0") and total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_platform_free_amount = (
                free_amount * fee_platform_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_platform_reward_amount = (
                reward_amount * fee_platform_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_platform_amount
        fee_platform_permanent_amount = (
            fee_platform_amount - fee_platform_free_amount - fee_platform_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate fee_agent amounts by credit type
    fee_agent_free_amount = Decimal("0")
    fee_agent_reward_amount = Decimal("0")
    fee_agent_permanent_amount = Decimal("0")

    if fee_agent_amount > Decimal("0") and total_amount > Decimal("0"):
        # Calculate proportions based on the formula
        if free_amount > Decimal("0"):
            fee_agent_free_amount = (
                free_amount * fee_agent_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        if reward_amount > Decimal("0"):
            fee_agent_reward_amount = (
                reward_amount * fee_agent_amount / total_amount
            ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

        # Calculate permanent amount as the remainder to ensure the sum equals fee_agent_amount
        fee_agent_permanent_amount = (
            fee_agent_amount - fee_agent_free_amount - fee_agent_reward_amount
        ).quantize(FOURPLACES, rounding=ROUND_HALF_UP)

    # Calculate base amounts by credit type using subtraction method
    base_free_amount = free_amount - fee_platform_free_amount - fee_agent_free_amount

    base_reward_amount = (
        reward_amount - fee_platform_reward_amount - fee_agent_reward_amount
    )

    base_permanent_amount = (
        permanent_amount - fee_platform_permanent_amount - fee_agent_permanent_amount
    )

    # 4. Update fee account - add credits
    memory_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_MEMORY,
        amount_details={
            CreditType.FREE: base_free_amount,
            CreditType.REWARD: base_reward_amount,
            CreditType.PERMANENT: base_permanent_amount,
        },
        event_id=event_id,
    )
    platform_fee_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_FEE,
        amount_details={
            CreditType.FREE: fee_platform_free_amount,
            CreditType.REWARD: fee_platform_reward_amount,
            CreditType.PERMANENT: fee_platform_permanent_amount,
        },
        event_id=event_id,
    )
    if fee_agent_amount > 0:
        agent_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.AGENT,
            owner_id=agent.id,
            amount_details={
                CreditType.FREE: fee_agent_free_amount,
                CreditType.REWARD: fee_agent_reward_amount,
                CreditType.PERMANENT: fee_agent_permanent_amount,
            },
            event_id=event_id,
        )

    # 5. Create credit event record

    # Get agent wallet address
    agent_data = await AgentData.get(agent.id)
    agent_wallet_address = agent_data.evm_wallet_address if agent_data else None

    event = CreditEventTable(
        id=event_id,
        account_id=user_account.id,
        event_type=EventType.MEMORY,
        user_id=user_id,
        upstream_type=UpstreamType.EXECUTOR,
        upstream_tx_id=message_id,
        direction=Direction.EXPENSE,
        agent_id=agent.id,
        message_id=message_id,
        start_message_id=start_message_id,
        model=agent.model,
        total_amount=total_amount,
        credit_type=credit_type,
        credit_types=details.keys(),
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=base_amount,
        base_original_amount=base_original_amount,
        base_llm_amount=base_llm_amount,
        base_free_amount=base_free_amount,
        base_reward_amount=base_reward_amount,
        base_permanent_amount=base_permanent_amount,
        fee_platform_amount=fee_platform_amount,
        fee_platform_free_amount=fee_platform_free_amount,
        fee_platform_reward_amount=fee_platform_reward_amount,
        fee_platform_permanent_amount=fee_platform_permanent_amount,
        fee_agent_amount=fee_agent_amount,
        fee_agent_free_amount=fee_agent_free_amount,
        fee_agent_reward_amount=fee_agent_reward_amount,
        fee_agent_permanent_amount=fee_agent_permanent_amount,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
        agent_wallet_address=agent_wallet_address,
    )
    session.add(event)

    # 4. Create credit transaction records
    # 4.1 User account transaction (debit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.PAY,
        credit_debit=CreditDebit.DEBIT,
        change_amount=total_amount,
        credit_type=credit_type,
        free_amount=free_amount,
        reward_amount=reward_amount,
        permanent_amount=permanent_amount,
    )
    session.add(user_tx)

    # 4.2 Memory account transaction (credit)
    memory_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=memory_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_BASE_MEMORY,
        credit_debit=CreditDebit.CREDIT,
        change_amount=base_amount,
        credit_type=credit_type,
        free_amount=base_free_amount,
        reward_amount=base_reward_amount,
        permanent_amount=base_permanent_amount,
    )
    session.add(memory_tx)

    # 4.3 Platform fee account transaction (credit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_fee_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECEIVE_FEE_PLATFORM,
        credit_debit=CreditDebit.CREDIT,
        change_amount=fee_platform_amount,
        credit_type=credit_type,
        free_amount=fee_platform_free_amount,
        reward_amount=fee_platform_reward_amount,
        permanent_amount=fee_platform_permanent_amount,
    )
    session.add(platform_tx)

    # 4.4 Agent fee account transaction (credit) - only if there's an agent fee
    if fee_agent_amount > 0:
        agent_tx = CreditTransactionTable(
            id=str(XID()),
            account_id=agent_account.id,
            event_id=event_id,
            tx_type=TransactionType.RECEIVE_FEE_AGENT,
            credit_debit=CreditDebit.CREDIT,
            change_amount=fee_agent_amount,
            credit_type=CreditType.REWARD,
            free_amount=fee_agent_free_amount,
            reward_amount=fee_agent_reward_amount,
            permanent_amount=fee_agent_permanent_amount,
        )
        session.add(agent_tx)

    # 5. Refresh session to get updated data
    await session.refresh(user_account)

    # 6. Return credit event model
    return CreditEvent.model_validate(event)
