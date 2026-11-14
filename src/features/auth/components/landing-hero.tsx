"use client";

import Link from "next/link";
import { ArrowDown, ArrowRight } from "lucide-react";
import { useTranslation } from "@/i18n/use-translation";
import { LandingHeroScene } from "./landing-hero-scene";
import styles from "./landing-hero.module.css";

export function LandingHero() {
  const { translate } = useTranslation();
  return (
    <section className={styles.hero} aria-labelledby="hero-title">
      <div className={styles.inner}>
        <div className={styles.copy} data-reveal>
          <p className={styles.eyebrow}>{translate("landingEvidence.heroEyebrow")}</p>
          <h1 id="hero-title" className={styles.heading}>
            <span>{translate("landingEvidence.heroLineOne")}</span>
            <em>{translate("landingEvidence.heroLineTwo")}</em>
          </h1>
          <p className={styles.description}>
            {translate("landingEvidence.heroDescriptionOne")}<br />
            {translate("landingEvidence.heroDescriptionTwo")}
          </p>
          <div className={styles.actions}>
            <Link className={styles.primary} href="/signup">{translate("landingEvidence.heroCta")}<ArrowRight size={20} aria-hidden="true" /></Link>
            <a className={styles.secondary} href="#why">{translate("landingEvidence.navWhy")}<ArrowDown size={17} aria-hidden="true" /></a>
          </div>
          <p className={styles.caption}>{translate("landingEvidence.heroCtaHint")}</p>
        </div>
        <LandingHeroScene />
      </div>
      <a className={styles.scrollCue} href="#why" aria-label={translate("landingEvidence.navWhy")}><ArrowDown size={24} aria-hidden="true" /></a>
    </section>
  );
}
