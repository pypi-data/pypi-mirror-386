# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .adaptive_card_invoke_action import AdaptiveCardInvokeAction
from .token_exchange_invoke_request import TokenExchangeInvokeRequest
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AdaptiveCardInvokeValue(AgentsModel):
    """AdaptiveCardInvokeResponse.

    Defines the structure that arrives in the Activity.Value for Invoke activity with Name of 'adaptiveCard/action'.

    :param action: The action of this adaptive card invoke action value.
    :type action: :class:`microsoft_agents.activity.adaptive_card_invoke_action.AdaptiveCardInvokeAction`
    :param authentication: The TokenExchangeInvokeRequest for this adaptive card invoke action value.
    :type authentication: :class:`microsoft_agents.activity.token_exchange_invoke_request.TokenExchangeInvokeRequest`
    :param state: The 'state' or magic code for an OAuth flow.
    :type state: str
    """

    action: AdaptiveCardInvokeAction = None
    authentication: TokenExchangeInvokeRequest = None
    state: NonEmptyString = None
