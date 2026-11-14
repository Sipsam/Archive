"use client";

import { useEffect, useRef, useState } from "react";

const durations = [3600, 3200, 3000, 3600];

/** A looping, local illustration. No wage calculation or server processing. */
export function useLandingStory() {
  const sceneRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLSpanElement>(null);
  const elapsed = useRef(0);
  const [stage, setStage] = useState(0);
  const [paused, setPaused] = useState(false);
  const [visible, setVisible] = useState(false);
  const [reduced, setReduced] = useState(false);
  const [manual, setManual] = useState(false);
  const [run, setRun] = useState(0);
  const [docking, setDocking] = useState(false);
  const playing = visible && !paused && !reduced;
  const layoutPlaying = visible && !reduced && (!paused || manual);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotion = () => {
      setReduced(media.matches);
      if (media.matches) {
        elapsed.current = 0;
        setStage(3);
        setPaused(true);
        setManual(true);
      }
    };
    updateMotion();
    media.addEventListener("change", updateMotion);
    return () => media.removeEventListener("change", updateMotion);
  }, []);

  useEffect(() => {
    const element = sceneRef.current;
    if (!element) return;
    let inView = !window.IntersectionObserver;
    const update = () => setVisible(inView && !document.hidden);
    const observer = window.IntersectionObserver ? new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      update();
    }, { threshold: 0.1 }) : undefined;
    observer?.observe(element);
    document.addEventListener("visibilitychange", update);
    update();
    return () => {
      observer?.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  useEffect(() => {
    const updateProgress = () => progressRef.current?.style.setProperty("--progress", String(elapsed.current / durations[stage]));
    updateProgress();
    if (!playing) return;
    let previous: number | undefined;
    let frame: number;
    const tick = (now: number) => {
      if (previous !== undefined) elapsed.current = Math.min(durations[stage], elapsed.current + now - previous);
      previous = now;
      updateProgress();
      if (elapsed.current >= durations[stage]) {
        elapsed.current = 0;
        setDocking(stage === 0);
        setStage((stage + 1) % durations.length);
        if (stage === durations.length - 1) setRun(value => value + 1);
        return;
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, stage, run]);

  const select = (next: number) => {
    elapsed.current = 0;
    setDocking(stage === 0 && next > 0);
    setStage(next);
    setPaused(true);
    setManual(true);
    setRun(value => value + 1);
  };
  const replay = () => {
    elapsed.current = 0;
    setDocking(false);
    setStage(0);
    setPaused(false);
    setManual(false);
    setRun(value => value + 1);
  };
  const toggle = () => {
    if (paused && manual) {
      setManual(false);
      setRun(value => value + 1);
    }
    setPaused(value => !value);
  };

  return {
    sceneRef, progressRef, stage, playing, paused, run, select, docking, layoutPlaying, replay,
    animated: !reduced && !manual,
    toggle,
  };
}
