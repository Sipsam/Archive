"use client";

import type { CSSProperties } from "react";
import { ArrowUpRight, CalendarDays, Coins, Link2, MessageCircle } from "lucide-react";
import { useTranslation } from "@/i18n/use-translation";
import styles from "./landing-evidence.module.css";

const arrears = [
  { year: 2024, amount: 1078, label: "landingEvidence.amount2024" },
  { year: 2025, amount: 1548, label: "landingEvidence.amount2025" },
] as const;
const findings = [
  { value: "55.7%", label: "landingEvidence.wagesMissing", scope: "landingEvidence.victimScope", icon: CalendarDays },
  { value: "34.4%", label: "landingEvidence.severanceMissing", scope: "landingEvidence.victimScope", icon: Coins },
  { value: "58.4%", label: "landingEvidence.communication", scope: "landingEvidence.complaintScope", icon: MessageCircle },
] as const;
const localFindings = [
  { value: 62.2, label: "landingEvidence.contractPartial" },
  { value: 51.6, label: "landingEvidence.contractUntranslated" },
  { value: 83.5, label: "landingEvidence.payslipReceived" },
  { value: 63.8, label: "landingEvidence.noResponse" },
] as const;

export function LandingEvidence() {
  const { translate } = useTranslation();
  return (
    <section id="why" className={styles.section} aria-labelledby="evidence-title">
      <div className={styles.inner}>
        <div className={styles.intro} data-reveal>
          <p className={styles.kicker}>{translate("landingEvidence.problemEyebrow")}</p>
          <h2 id="evidence-title">{translate("landingEvidence.sectionTitle")}</h2>
        </div>
        <article className={styles.research} aria-labelledby="arrears-title" data-research="ministry">
          <div data-reveal>
          <p className={styles.kicker}><span aria-hidden="true">01</span>{translate("landingEvidence.ministryEyebrow")}</p>
          <h3 id="arrears-title" className={styles.title}>{translate("landingEvidence.trendLineOne")}<br />{translate("landingEvidence.trendLineTwo")} <em>{translate("landingEvidence.trendEmphasis")}</em></h3>
          <p className={styles.subtitle}>{translate("landingEvidence.trendSubtitle")}</p>
          </div>
          <div className={styles.trendLayout}>
            <div data-reveal>
              <p className={styles.metricLabel}>{translate("landingEvidence.totalLabel")}</p>
              <p className={styles.total}>{translate("landingEvidence.amount2025")}</p>
              <dl className={styles.secondaryMetrics}>
                <div><dt>{translate("landingEvidence.changeLabel")}</dt><dd>+43.6<span>%</span></dd></div>
                <div><dt>{translate("landingEvidence.workersLabel")}</dt><dd>{translate("landingEvidence.workersTotal")}</dd></div>
              </dl>
            </div>
            <figure className={styles.chart} aria-describedby="ministry-scope" data-reveal style={{"--delay": "120ms"} as CSSProperties}>
              <figcaption>{translate("landingEvidence.trendTitle")}</figcaption>
              <div className={styles.plot}>
                <span className={styles.zero} aria-hidden="true">0</span>
                {arrears.map(({ year, amount, label }) => (
                  <div className={styles.column} key={year}>
                    <div className={styles.measure} style={{ "--height": `${amount / 1548 * 100}%` } as CSSProperties}>
                      <strong>{translate(label)}</strong>
                      <div className={styles.bar} data-testid="arrears-bar" data-amount={amount} aria-hidden="true" />
                    </div>
                    <span className={styles.year}>{year}</span>
                  </div>
                ))}
              </div>
            </figure>
          </div>
          <p className={styles.insight} data-reveal>{translate("landingEvidence.smallWorkplaces")}</p>
          <footer className={styles.sources} data-reveal>
            <a href="https://www.yna.co.kr/view/AKR20260908041700054">{translate("landingEvidence.trendSource")}<ArrowUpRight size={14} aria-hidden="true" /></a>
            <p id="ministry-scope">{translate("landingEvidence.trendScope")}</p>
          </footer>
        </article>
        <article className={styles.research} aria-labelledby="victim-title" data-research="human-rights">
          <div data-reveal>
          <p className={styles.kicker}><span aria-hidden="true">02</span>{translate("landingEvidence.studyEyebrow")}</p>
          <h3 id="victim-title" className={styles.title}>{translate("landingEvidence.victimLineOne")}<br />{translate("landingEvidence.victimLineTwo")}</h3>
          </div>
          <dl className={styles.findings}>
            {findings.map(({value, label, scope, icon: Icon}, index) => (
              <div key={label} data-reveal style={{"--delay": `${index * 90}ms`} as CSSProperties}>
                <Icon size={31} strokeWidth={1.6} aria-hidden="true" />
                <dt>{translate(label)}</dt><dd>{value}</dd>
                <dd className={styles.findingScope}>{translate(scope)}</dd>
              </div>
            ))}
          </dl>
          <footer className={styles.sources} data-reveal>
            <div className={styles.sourceLinks}>
              <a href="https://humanrights.go.kr/base/board/read?boardManagementNo=17&boardNo=7610155&menuLevel=3&menuNo=91&page=1">{translate("landingEvidence.studySource")}<ArrowUpRight size={14} aria-hidden="true" /></a>
              <a href="https://www.hankookilbo.com/news/article/amp/A2024042516040003835">{translate("landingEvidence.studyCoverage")}<ArrowUpRight size={14} aria-hidden="true" /></a>
            </div>
            <p>{translate("landingEvidence.studyScope")}</p>
          </footer>
        </article>
        <article className={styles.research} aria-labelledby="understanding-title" data-research="geoje">
          <p className={styles.kicker} data-reveal><span aria-hidden="true">03</span>{translate("landingEvidence.localEyebrow")}</p>
          <div className={styles.localLayout}>
            <div data-reveal>
              <h3 id="understanding-title" className={styles.title}>{translate("landingEvidence.localLineOne")}<br />{translate("landingEvidence.localLineTwo")}<br /><em>{translate("landingEvidence.localEmphasis")}</em></h3>
              <p className={styles.localDescription}>{translate("landingEvidence.localDescription")}</p>
            </div>
            <dl className={styles.localMetrics}>
              {localFindings.map(({value, label}, index) => (
                <div key={label} data-reveal style={{"--delay": `${index * 90}ms`} as CSSProperties}>
                  <dt>{translate(label)}</dt><dd>{value}%</dd>
                  <dd className={styles.rule} aria-hidden="true"><span style={{ width: `${value}%` }} /></dd>
                </div>
              ))}
            </dl>
          </div>
          <footer className={styles.sources} data-reveal>
            <a href="https://www.gjcwc.org/Notice/?bmode=view&idx=151871180">{translate("landingEvidence.localSource")}<ArrowUpRight size={14} aria-hidden="true" /></a>
            <p>{translate("landingEvidence.localScope")}</p>
          </footer>
        </article>
        <div className={styles.bridge} data-reveal><Link2 size={33} strokeWidth={2.4} aria-hidden="true" /><p>{translate("landingEvidence.bridgeLineOne")}<br /><em>{translate("landingEvidence.bridgeLineTwo")}</em></p></div>
      </div>
    </section>
  );
}
