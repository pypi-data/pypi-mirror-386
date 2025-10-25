import httpx
import json
from typing import Awaitable, List, Optional, Callable, Any
from pydantic import SecretStr
import asyncio


class Aeon:
    api_key: SecretStr
    project_id: int
    agent: Optional[str] = None
    endpoint: Optional[str] = "https://withaeon.com"
    initialized: bool = False
    heartbeat_started = False

    @staticmethod
    def init(
        api_key: str,
        project_id: int,
        agent: Optional[str] = None,
        endpoint: Optional[str] = "https://withaeon.com",
    ):
        if Aeon.initialized:
            raise RuntimeError("Aeon has already been initialized")

        Aeon.initialized = True
        Aeon.api_key = SecretStr(api_key)
        Aeon.agent = agent
        Aeon.endpoint = endpoint
        Aeon.project_id = project_id

        print("Aeon initialized with endpoint: ", Aeon.endpoint)

    @staticmethod
    async def track_session(costs: float, model: str):
        """
        Send session data to API
        """

        print("Sending session")

        if not Aeon.agent:
            raise ValueError(
                "Agent name is not set. Please provide a valid agent name."
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/sessions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"{Aeon.api_key.get_secret_value()}",
                    },
                    json={
                        "agent_name": Aeon.agent,
                        "model": model,
                        "costs": costs,
                    },
                )

                print(response)

        except Exception as e:
            print("Error: ", e)

    # El to puede ser undefined, y si es undefined flink se encarga de enrutarlo automaticamente
    @staticmethod
    async def send_task(
        event: str,
        context: Optional[List[Any]] = None,
        to: Optional[str] = None,
        from_: Optional[str] = None,
    ):
        """
        Send a task to an agent

        Parameters:
            task (dict): Information of the task recipient and the event to be send.
                Expected keys:
                - 'event' (str): What the agent should do.
                - 'context' (str): Optional[List[Any]] context of the task (handled in automatic orchestration).
                - 'to' (str): Which agent to send the message.
                - 'from_' (str, optional): Agent that sends the event (handled internally).
        """

        if not Aeon.agent:
            raise ValueError(
                "Agent name is not set. Please provide a valid agent name."
            )

        if not from_:
            from_ = Aeon.agent

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/send",
                    headers={
                        "Authorization": Aeon.api_key.get_secret_value(),
                        "Content-Type": "application/json",
                    },
                    json={
                        "to": to,
                        "from": from_,
                        "event": event,
                        "context": context,
                    },
                    timeout=30.0,
                )

                print(f"Task sent")
        except Exception as e:
            print("Error: ", e)

    @staticmethod
    async def listen(callback: Callable[[str], Awaitable[str]]):
        """
        Listen to the server for tasks to execute

        Parameters:
            callback (Callable[[str], Awaitable[str]]): Asynchronous function to call when the agent receives a task.
                Receives the event as a string argument.
        """

        if not Aeon.initialized:
            raise RuntimeError("Aeon has not been initialized. Call Aeon.init() first.")

        if not Aeon.agent:
            raise ValueError(
                "Agent name is not set. Please provide a valid agent name."
            )

        # Update the agent status periodically in the background
        asyncio.create_task(Aeon._heartbeat())

        await Aeon._handle_tasks(callback)

    @staticmethod
    async def _handle_tasks(callback: Callable[[str], Awaitable[str]]):
        """
        Listen to the server for tasks to execute

        Parameters:
            callback (Callable[[str], Awaitable[str]]): Asynchronous function to call when the agent receives a task.
                Receives the event as a string argument.
        """

        if not Aeon.initialized:
            raise RuntimeError("Aeon has not been initialized. Call Aeon.init() first.")

        if not Aeon.agent:
            raise ValueError(
                "Agent name is not set. Please provide a valid agent name."
            )

        # Store the trigger_id to send failed status in case something goes wrong
        trigger_id = None

        url = f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/listen?agent={Aeon.agent}"

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers={"Authorization": Aeon.api_key.get_secret_value()},
                ) as response:

                    if response.status_code != 200:
                        raise Exception(f"Failed to connect: {response.status_code}")

                    # if not Aeon.heartbeat_started:
                    #     asyncio.create_task(Aeon._heartbeat())
                    #     Aeon.heartbeat_started = True

                    async for line in response.aiter_lines():
                        if not line or line.startswith(":"):
                            continue

                        # Process SSE format
                        if line.startswith("data: "):
                            data_str = line[6:]

                            try:
                                task = json.loads(data_str)
                                event = task.get("event")
                                trigger_id = task.get("id")
                                context = task.get("context")
                                from_ = task.get("from")

                                if not event:
                                    continue

                                print(f"Executing task: {task}")

                                try:
                                    response = await callback(event)

                                    # Send next task
                                    await Aeon.send_task(
                                        event=response,
                                        from_=Aeon.agent,
                                        context=[
                                            *(context or []),
                                            {
                                                "event": event,
                                                "from": from_,
                                                "to": Aeon.agent,
                                                "response": response,
                                            },
                                        ],
                                    )

                                    await Aeon.send_trigger_status(
                                        trigger_id=trigger_id, status="completed"
                                    )

                                except Exception as e:
                                    print(f"Error: {e}")
                                    print("Sending failed status...")

                                    # If something failes, update the status to 'failed'
                                    await Aeon.send_trigger_status(
                                        trigger_id=trigger_id, status="failed"
                                    )

                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            print(f"Connection error: {e}")
            raise

    @staticmethod
    async def send_trigger_status(status: str, trigger_id: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/triggers/{trigger_id}",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": Aeon.api_key.get_secret_value(),
                    },
                    json={"status": status},
                )
                print(response)
        except Exception as e:
            print(f"Trigger status error: {e}")
            raise

    @staticmethod
    async def _heartbeat():
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/heartbeat",
                        headers={
                            "Authorization": f"{Aeon.api_key.get_secret_value()}",
                        },
                        json={"agent_name": Aeon.agent, "status": "active"},
                    )
            except Exception as e:
                print(f"Heartbeat error: {e}")
            await asyncio.sleep(15)  # every 15 seconds

    @staticmethod
    async def orchestrate(event: str):
        """
        Start automatic agent orchestration.

        Parameters:
            event (str): Coordinates all agents to perform the task associated with the given event.
        """

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{Aeon.endpoint}/api/v1/projects/{Aeon.project_id}/agents/send",
                    headers={
                        "Authorization": Aeon.api_key.get_secret_value(),
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": "Orchestrator",
                        "event": event,
                    },
                    timeout=30.0,
                )

                print(f"Starting orchestration...")
        except Exception as e:
            print("Error: ", e)
