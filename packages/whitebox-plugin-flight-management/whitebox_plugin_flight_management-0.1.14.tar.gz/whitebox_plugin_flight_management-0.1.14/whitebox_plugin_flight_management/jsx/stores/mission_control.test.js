import { act } from "@testing-library/react";
import useMissionControlStore from "./mission_control";

describe("useMissionControlStore", () => {
  const getState = useMissionControlStore.getState;
  const setState = useMissionControlStore.setState;

  let socketsSendMock;
  let apiGetPathMock;
  let apiClientGetMock;

  beforeEach(async () => {
    socketsSendMock = vi.fn();
    apiGetPathMock = vi.fn();
    apiClientGetMock = vi.fn();

    globalThis.Whitebox = {
      sockets: {
        send: socketsSendMock,
        addEventListener: vi.fn(),
      },
      api: {
        getPluginProvidedPath: apiGetPathMock,
        client: {
          get: apiClientGetMock,
        },
      },
    };

    // Dynamically import the module under test (ensures it reads our Whitebox)
    vi.resetModules();
  });

  describe("key moment management", () => {
    it("recordKeyMoment sends correct socket message", () => {
      getState().recordKeyMoment();
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.key_moment.record",
      });
    });

    it("finishKeyMoment sends correct socket message", () => {
      getState().finishKeyMoment();
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.key_moment.finish",
      });
    });

    it("updateKeyMoment sends correct socket message with updates", () => {
      const updates = { name: "Updated Key Moment" };
      getState().updateKeyMoment(1, updates);
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.key_moment.update",
        key_moment_id: 1,
        ...updates,
      });
    });

    it("deleteKeyMoment sends correct socket message", () => {
      getState().deleteKeyMoment(1);
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.key_moment.delete",
        key_moment_id: 1,
      });
    });
  });

  describe("utility functions", () => {
    it("isKeyMomentActive returns correct state", () => {
      const keyMoment = { id: 1, ended_at: null };
      getState().setActiveKeyMoment(keyMoment);
      expect(getState().isKeyMomentActive()).toBe(true);

      const endedKeyMoment = { ...keyMoment, ended_at: "2025-01-01T01:00:00Z" };
      getState().setActiveKeyMoment(endedKeyMoment);
      expect(getState().isKeyMomentActive()).toBe(false);
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("helpers", () => {
    it("setActiveFlightSession and isFlightSessionActive", () => {
      const s = getState();
      expect(s.isReady).toBe(false);
      expect(s.activeFlightSession).toBe(null);
      expect(s.isFlightSessionActive()).toBeFalsy();

      const active = {
        id: 1,
        started_at: "2025-01-01T00:00:00Z",
        ended_at: null,
      };
      s.setActiveFlightSession(active);
      expect(getState().isReady).toBe(true);
      expect(getState().activeFlightSession).toEqual(active);
      expect(getState().isFlightSessionActive()).toBe(true);

      const ended = { ...active, ended_at: "2025-01-01T01:00:00Z" };
      getState().setActiveFlightSession(ended);
      expect(getState().isFlightSessionActive()).toBeFalsy();
    });
  });

  describe("flight session management", () => {
    it("startFlightSession sends socket message and flips isLoaded to false", async () => {
      // Make it true first so we see it flip to false
      getState().setActiveFlightSession({ id: 1, ended_at: null });

      await getState().startFlightSession();
      expect(getState().isReady).toBe(false);
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.start",
        takeoff_location: {},
        arrival_location: {},
        waypoints: [],
      });
    });

    it("endFlightSession sends socket message and flips isLoaded to false", async () => {
      // Make it true first so we see it flip to false
      getState().setActiveFlightSession({ id: 1, ended_at: null });

      await getState().endFlightSession();
      expect(getState().isReady).toBe(false);
      expect(socketsSendMock).toHaveBeenCalledWith("flight", {
        type: "flight.end",
      });
    });

    it("toggleFlightSession calls end when active and start when not active", async () => {
      socketsSendMock.mockClear();

      // Active session -> should end
      getState().setActiveFlightSession({ id: 1, ended_at: null });
      await getState().toggleFlightSession();
      expect(socketsSendMock).toHaveBeenLastCalledWith("flight", {
        type: "flight.end",
      });

      // Ended session -> should start
      getState().setActiveFlightSession({
        id: 1,
        ended_at: "2025-01-01T01:00:00Z",
      });
      await getState().toggleFlightSession();
      expect(socketsSendMock).toHaveBeenLastCalledWith("flight", {
        type: "flight.start",
        takeoff_location: {},
        arrival_location: {},
        waypoints: [],
      });

      // No session -> should start
      setState({ flightSession: null });
      await getState().toggleFlightSession();
      expect(socketsSendMock).toHaveBeenLastCalledWith("flight", {
        type: "flight.start",
        takeoff_location: {},
        arrival_location: {},
        waypoints: [],
      });
    });
  });

  describe("flight sessions fetching", () => {
    it("fetchFlightSessions success sets data and state", async () => {
      const fakeUrl = "/api/flight-sessions";
      const payload = [{ id: 1 }, { id: 2 }];
      apiGetPathMock.mockReturnValue(fakeUrl);
      apiClientGetMock.mockResolvedValue({ data: payload });

      const ok = await getState().fetchFlightSessions();
      // expect(ok).toBe(true);
      expect(apiGetPathMock).toHaveBeenCalledWith("flight.flight-session-list");
      expect(getState().flightSessions).toEqual(payload);
      expect(getState().fetchState).toBe("loaded");

      // getFlightSessions returns [] if null, otherwise the array as-is
      expect(getState().getFlightSessions()).toEqual(payload);
      setState({ flightSessions: null });
      expect(getState().getFlightSessions()).toEqual([]);
    });

    it("fetchFlightSessions failure sets fetchState=error and returns false", async () => {
      apiGetPathMock.mockReturnValue("/api/flight-sessions");
      apiClientGetMock.mockRejectedValue(new Error("boom"));

      const ok = await getState().fetchFlightSessions();
      expect(ok).toBe(false);
      expect(getState().fetchState).toBe("error");
    });
  });

  describe("playback controls", () => {
    it("play/pause emit corresponding events and toggle state", async () => {
      const mockSyncPlayers = vi.fn();
      const mockPlaybackTime = vi.fn();
      const mockScheduleStop = vi.fn();
      const mockEmitPlaybackTime = vi.fn();
      await act(async () => {
        await setState({
          syncPlayers: mockSyncPlayers,
          getPlaybackTime: mockPlaybackTime,
          _scheduleStopWhenEnded: mockScheduleStop,
          _emitPlaybackTime: mockEmitPlaybackTime,
        });
      });

      const events = [];
      const unsub = getState().on("playback.play", () => events.push("play"));
      const unsub2 = getState().on("playback.pause", () =>
        events.push("pause")
      );

      expect(getState().playbackStatus).toBe("stopped");

      getState().playbackPlay();
      expect(getState().playbackStatus).toBe("playing");
      expect(mockSyncPlayers).toHaveBeenCalledTimes(1);
      expect(mockScheduleStop).toHaveBeenCalledTimes(1);
      expect(mockEmitPlaybackTime).toHaveBeenCalledTimes(0);

      getState().playbackPause();
      expect(getState().playbackStatus).toBe("paused");
      expect(mockSyncPlayers).toHaveBeenCalledTimes(2);
      expect(mockEmitPlaybackTime).toHaveBeenCalledWith(
        mockPlaybackTime.returnValue
      );
      // This one should not be called on pause, nothing to schedule
      expect(mockScheduleStop).toHaveBeenCalledTimes(1);
      expect(getState().playbackTimeLastSet).toBe(mockPlaybackTime.returnValue);

      expect(events).toEqual(["play", "pause"]);

      unsub();
      unsub2();
    });

    it("playbackToggle switches between play and pause", async () => {
      const mockPlay = vi.fn();
      const mockPause = vi.fn();

      await act(async () => {
        setState({
          playbackPlay: mockPlay,
          playbackPause: mockPause,
          playbackStatus: "playing",
        });
      });

      await act(async () => {
        await getState().playbackToggle();
      });
      expect(mockPlay).toHaveBeenCalledTimes(0);
      expect(mockPause).toHaveBeenCalledTimes(1);

      await act(async () => {
        await setState({ playbackStatus: "paused" });
      });

      await act(async () => {
        await getState().playbackToggle();
      });
      expect(mockPlay).toHaveBeenCalledTimes(1);
      expect(mockPause).toHaveBeenCalledTimes(1);
    });

    it('setPlaybackTime handles changes, ending, and emits "playback.time"', () => {
      const session = {
        started_at: "2025-01-01T00:00:00Z",
        ended_at: "2025-01-01T00:01:40Z", // 100s total
      };
      setState({
        playbackFlightSession: session,
        // Set `paused` state as the initial `stopped` state has no seeking
        playbackStatus: "paused",
      });

      const times = [];
      const unsub = getState().on("playback.time", (t) => times.push(t));

      // within range
      getState().setPlaybackTime(42);
      expect(getState().getPlaybackTime()).toBe(42);

      // below range
      getState().setPlaybackTime(-5);
      expect(getState().getPlaybackTime()).toBe(0);

      // above range (reset to 0)
      getState().setPlaybackTime(150);
      expect(getState().getPlaybackTime()).toBe(0);

      expect(times).toEqual([42, 0, 100]);
      unsub();
    });
  });

  describe("mode slice", () => {
    it("enterFlightMode sets mode and clears playbackFlightSession", () => {
      setState({
        mode: "playback",
        playbackFlightSession: { id: 7 },
      });
      getState().enterFlightMode();
      expect(getState().mode).toBe("flight");
      expect(getState().playbackFlightSession).toBeNull();
    });

    it("enterPlaybackMode sets mode and session; calls playbackReset when switching from non-playback", () => {
      // inject a spy into state for playbackReset
      const spy = vi.fn();
      setState({ mode: "flight", playbackReset: spy });

      const fs = {
        id: 99,
        started_at: "2025-01-01T00:00:00Z",
        ended_at: "2025-01-01T00:10:00Z",
      };
      getState().enterPlaybackMode(fs);

      expect(spy).toHaveBeenCalledTimes(1);
      expect(getState().mode).toBe("playback");
      expect(getState().playbackFlightSession).toEqual(fs);
    });

    it("enterPlaybackMode does NOT call playbackReset when already in playback", () => {
      const spy = vi.fn();
      setState({ mode: "playback", playbackReset: spy });

      getState().enterPlaybackMode({ id: 1 });
      expect(spy).not.toHaveBeenCalled();
    });
  });
});
