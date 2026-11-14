"use client";

import { CalendarDays, Check, CheckCheck, Clock3, FileText, FolderOpen, Link2, Pause, Play, RotateCcw, Wallet } from "lucide-react";
import type { CSSProperties } from "react";
import { useTranslation } from "@/i18n/use-translation";
import { useLandingStory } from "./use-landing-story";
import styles from "./landing-hero.module.css";

export function LandingHeroScene() {
  const { translate } = useTranslation();
  const { sceneRef, progressRef, stage, playing, animated, run, select, toggle, paused, docking, layoutPlaying, replay } = useLandingStory();
  const steps = [translate("landingEvidence.stepRead"), translate("landingEvidence.stepVerify"), translate("landingEvidence.stepConnect"), translate("landingEvidence.stepCompare")];
  const titles = [translate("auth.landing_span8"), translate("landingEvidence.verifyTitle"), translate("landingEvidence.depositTitle"), translate("landingEvidence.compareTitle")];
  const documents = [
    { label: translate("auth.landing_attendance"), icon: CalendarDays },
    { label: translate("auth.landing_payslip"), icon: FileText },
    { label: translate("auth.landing_deposit"), icon: Wallet },
  ];
  const files = [
    { label: translate("auth.landing_contract"), file: translate("auth.landing_contract_2"), status: translate("auth.landing_confirm_2"), icon: FileText },
    { label: translate("auth.landing_attendance"), file: translate("auth.landing_attendance_2"), status: translate("auth.landing_time_confirm"), icon: Clock3 },
    { label: translate("auth.landing_payslip"), file: translate("auth.landing_payslip_2"), status: translate("auth.landing_amount_confirm"), icon: FileText },
    { label: translate("auth.landing_deposit"), file: translate("auth.landing_deposit_case"), status: translate("auth.landing_transaction_link"), icon: Wallet },
  ];
  const won = translate("common.won");

  return (
    <figure className={styles.figure} aria-labelledby="hero-scene-caption" data-reveal style={{ "--delay": "120ms" } as CSSProperties}>
      <div className={styles.story} data-stage={stage} data-playing={playing} data-animate={animated} data-docking={docking} data-layout-playing={layoutPlaying}>
        <div className={styles.scene} ref={sceneRef} data-story-scene>
          <div className={styles.orbit} aria-hidden="true" />
          <div className={styles.ambient} aria-hidden="true"><div className={styles.halo} /></div>
          {stage >= 1 && <>
          <svg className={styles.connections} viewBox="0 0 700 500" fill="none" aria-hidden="true" data-story-connections>
            {["M145 86C230 86 172 250 232 250", "M145 250H232", "M145 414C230 414 172 250 232 250"].map(path => (
              <g key={path}><path d={path} className={styles.connection} /><path d={path} className={styles.pulse} /></g>
            ))}
            <circle cx="232" cy="250" r="5" fill="currentColor" />
          </svg>
          <div className={styles.documents} aria-hidden="true" data-story-documents>
            {documents.map(({ label, icon: Icon }, index) => (
              <div className={styles.document} data-active={stage === 3 || stage === index} key={label}>
                <span className={styles.documentLabel}><Icon size={20} />{label}</span>
                <span className={styles.documentLines}><i /><i /><i /></span>
                <Check className={styles.documentCheck} size={16} />
                {index === 1 && <span className={styles.scan} />}
              </div>
            ))}
          </div>
          </>}
          <div className={styles.result} data-story-card>
            <div className={styles.resultHeader}><span>{translate("auth.landing_library_example")}</span><span className={styles.stageTag}>{String(stage + 1).padStart(2, "0")} / 04</span></div>
            <div className={styles.sceneTitle}>
              {stage === 0 && <FolderOpen size={24} aria-hidden="true" />}
              <h2>{titles[stage]}</h2>
              {stage === 0 && <span className={styles.company}>{translate("auth.landing_div24")}</span>}
            </div>
            <div id="hero-story-panel" className={styles.panel} key={`${run}-${stage}`} role="region" aria-label={steps[stage]}>
              {stage === 0 && <>
                <div className={styles.paperFan} aria-hidden="true">{files.map(({ icon: Icon }, index) => <span key={index} style={{ "--i": index } as CSSProperties}><Icon /></span>)}</div>
                <ul className={styles.collection}>
                  {files.map(({ label, file, status, icon: Icon }, index) => <li className={styles.fileRow} key={file} style={{ "--i": index } as CSSProperties}>
                    <span className={styles.fileIcon}><Icon size={21} aria-hidden="true" /></span>
                    <span className={styles.fileText}><strong>{label}</strong><small>{file}</small></span>
                    <span className={styles.fileStatus}>{status}<Check size={13} aria-hidden="true" /></span>
                  </li>)}
                </ul>
                <p className={styles.libraryNote}><CheckCheck size={17} aria-hidden="true" />{translate("auth.landing_workplace_period")}</p>
              </>}
              {stage === 1 && <>
                <div className={styles.verify}>
                  <div className={styles.paper}>
                    <span className={styles.smallLabel}>{translate("auth.landing_original_page")}</span>
                    <FileText size={26} aria-hidden="true" />
                    <span className={styles.paperLines} aria-hidden="true"><i /><i /><i /></span>
                    <span>{translate("auth.landing_netPay")}</span>
                    <strong className={styles.highlight}>2,100,000<small>{won}</small></strong>
                  </div>
                  <div className={styles.extracted}>
                    <span className={styles.smallLabel}>{translate("auth.landing_div9")}</span>
                    <strong>2,100,000<small>{won}</small></strong>
                    <span className={styles.manual}><Check size={13} aria-hidden="true" />{translate("landingEvidence.manualExample")}</span>
                  </div>
                </div>
                <p className={styles.note}>{translate("landingEvidence.verifyNote")}</p>
              </>}
              {stage === 2 && <>
                <div className={styles.transfers}>
                  {[{ date: translate("landingEvidence.depositDateTen"), amount: "1,500,000" }, { date: translate("landingEvidence.depositDateFifteen"), amount: "500,000" }].map(({ date, amount }) => <div className={styles.transfer} key={date}><span>{date}</span><strong>{amount}<small>{won}</small></strong><Link2 size={19} aria-hidden="true" /></div>)}
                </div>
                <div className={styles.subtotal}><span>{translate("auth.landing_link_deposit_sum")}</span><strong>2,000,000<small>{won}</small></strong></div>
                <p className={styles.note}>{translate("landingEvidence.depositNote")}</p>
              </>}
              {stage === 3 && <>
                <dl className={styles.amounts}>
                  <div><dt>{translate("auth.landing_payslip_netPay")}</dt><dd>2,100,000<small>{won}</small></dd></div>
                  <div><dt>{translate("auth.landing_link_deposit_sum")}</dt><dd>2,000,000<small>{won}</small></dd></div>
                </dl>
                <div className={styles.difference}><span>{translate("landingEvidence.heroDifference")}</span><strong>100,000<small>{won}</small></strong></div>
                <p className={styles.note}>{translate("auth.landing_difference_unpaid")}</p>
              </>}
            </div>
          </div>
        </div>
        <p id="hero-scene-caption" className={styles.sceneCaption}>{translate("landingEvidence.heroSceneDescription")}</p>
        <div className={styles.steps} role="group" aria-label={translate("landingEvidence.storySteps")}>
          {steps.map((label, index) => <button type="button" className={styles.step} data-complete={index < stage} aria-pressed={stage === index} aria-controls="hero-story-panel" key={label} onClick={() => select(index)}>
            <span className={styles.stepNumber} aria-hidden="true">{index < stage ? <Check size={13} /> : index + 1}</span>
            <span>{label}</span>
            {stage === index && <span className={styles.progress} ref={progressRef} aria-hidden="true" />}
          </button>)}
        </div>
        <div className={styles.playback}>
          <button className={styles.motionControl} type="button" onClick={toggle} aria-pressed={paused}>
            {paused ? <Play size={14} aria-hidden="true" /> : <Pause size={14} aria-hidden="true" />}
            {translate(paused ? "landingEvidence.resumeMotion" : "landingEvidence.pauseMotion")}
          </button>
          <button className={styles.motionControl} type="button" onClick={replay}>
            <RotateCcw size={14} aria-hidden="true" />{translate("landingEvidence.replayMotion")}
          </button>
          <span className={styles.playbackHint}>{translate("landingEvidence.storyHint")}</span>
        </div>
      </div>
    </figure>
  );
}
