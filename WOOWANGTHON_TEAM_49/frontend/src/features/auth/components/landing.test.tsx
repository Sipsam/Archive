// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextIntlClientProvider } from 'next-intl';
import { catalogs } from '@/i18n/catalog.generated';
import { TranslationLocaleContext } from '@/i18n/use-translation';
import type { Locale } from '@/i18n/config';
vi.mock('@/i18n/language-provider', () => ({ useLanguage: () => ({locale:'ko', pending:false, error:null, select:vi.fn()}) }));
function renderLanding(locale: Locale = 'ko') {
  return render(<NextIntlClientProvider locale={locale} messages={catalogs[locale]}><TranslationLocaleContext.Provider value={locale}><Landing /></TranslationLocaleContext.Provider></NextIntlClientProvider>);
}
import { Landing } from "./landing";
vi.mock("@/features/auth/hooks/use-auth", () => ({ useAuth: () => ({status: "anonymous"}) }));

beforeEach(() => {
  vi.stubGlobal("matchMedia", vi.fn(() => ({
    matches: true,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })));
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

it("starts with the new wage question, routes to signup and retains the existing features", () => {
  renderLanding();
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("내 급여,제대로 받았을까요?");
  expect(screen.getByRole("link", { name: "내 급여 확인 시작하기" })).toHaveAttribute("href", "/signup");
  expect(screen.getByRole("link", { name: "로그인" })).toHaveAttribute("href", "/login");
  expect(screen.getByRole("link", { name: "시작하기" })).toHaveAttribute("href", "/signup");
  expect(screen.getByRole("link", { name: "월급잇다 시작하기" })).toHaveAttribute("href", "/signup");
  expect(document.getElementById('gather')).toBeVisible();
  expect(document.getElementById('calculate')).toBeVisible();
  expect(screen.getAllByText('차이가 곧 확정 미지급액을 의미하지는 않아요.')).toHaveLength(2);
  expect(screen.getAllByRole('link', {name:'왜 필요한가요?'}).every(link => link.getAttribute('href') === '#why')).toBe(true);
  expect(screen.getByText(/AI 답변은 참고용/)).toBeVisible();
  expect(screen.getByText(/제품 화면 속 문서와 금액은/)).toBeVisible();
});

it('presents three source-backed studies in order without conflating their populations', () => {
  renderLanding();
  const evidence = document.getElementById('why')!;
  expect([...evidence.querySelectorAll('article')].map(article => article.dataset.research)).toEqual(['ministry', 'human-rights', 'geoje']);
  const [ministry, humanRights, geoje] = [...evidence.querySelectorAll('article')];
  expect(within(ministry).getAllByText('1,548억 원')).toHaveLength(2);
  expect(within(ministry).getByText('30,684명')).toBeVisible();
  expect(within(ministry).getByText(/전체 외국인 근로자의 피해 경험률은 아니에요/)).toBeVisible();
  expect(within(humanRights).getByText('34.4%')).toBeVisible();
  expect(within(humanRights).getAllByText('임금체불 피해 경험자 응답')).toHaveLength(2);
  expect(within(humanRights).getByText('진정 경험자 응답')).toBeVisible();
  expect(within(geoje).getByText('83.5%').closest('div')).toHaveTextContent('임금명세서 수령');
  expect(within(geoje).getByText(/전국 대표 통계는 아니에요/)).toBeVisible();
  expect(evidence).not.toHaveTextContent(/379명|303명|177명|467명|34\.3%/);
  const sources = [...evidence.querySelectorAll('a')].map(link => link.href);
  expect(sources).toContain('https://www.yna.co.kr/view/AKR20260908041700054');
  expect(sources).toContain('https://www.gjcwc.org/Notice/?bmode=view&idx=151871180');
  expect(sources.some(url => url.includes('humanrights.go.kr'))).toBe(true);
});

it('can pause motion and stops decorative animation outside the viewport', async () => {
  let notify: IntersectionObserverCallback | undefined;
  const disconnect = vi.fn();
  vi.stubGlobal('matchMedia', vi.fn(() => ({matches:false, addEventListener:vi.fn(), removeEventListener:vi.fn()})));
  vi.stubGlobal('IntersectionObserver', class {
    constructor(private callback: IntersectionObserverCallback) {}
    observe(element: Element) { if (element.parentElement?.hasAttribute('data-stage')) notify = this.callback; }
    unobserve() {}
    disconnect = disconnect;
  });
  const user = userEvent.setup();
  const view = renderLanding();
  const scene = document.querySelector('[data-playing]')!;
  const enter = (isIntersecting: boolean) => act(() => notify?.([{isIntersecting} as IntersectionObserverEntry], {} as IntersectionObserver));
  expect(scene).toHaveAttribute('data-playing', 'false');
  enter(true);
  expect(scene).toHaveAttribute('data-playing', 'true');
  await user.click(screen.getByRole('button', {name:'애니메이션 일시정지'}));
  expect(scene).toHaveAttribute('data-playing', 'false');
  expect(screen.getByRole('button', {name:'애니메이션 재생'})).toHaveAttribute('aria-pressed', 'true');
  enter(false);
  await user.click(screen.getByRole('button', {name:'애니메이션 재생'}));
  expect(scene).toHaveAttribute('data-playing', 'false');
  enter(true);
  expect(scene).toHaveAttribute('data-playing', 'true');
  view.unmount();
  expect(disconnect).toHaveBeenCalled();
});

it('offers all four readable manual stages with reduced motion and keeps differences unconfirmed', async () => {
  const user = userEvent.setup();
  renderLanding();
  const steps = screen.getByRole('group', {name:'급여 확인 과정 미리보기'});
  const choose = (name: string) => user.click(within(steps).getByRole('button', {name}));
  expect(screen.getByRole('region', {name:'차이 확인'})).toHaveTextContent('차이가 곧 확정 미지급액을 의미하지는 않아요.');
  expect(document.querySelector('[data-playing]')).toHaveAttribute('data-playing', 'false');
  await choose('자료 모으기');
  expect(document.querySelector('[data-story-documents]')).toBeNull();
  expect(document.querySelector('[data-story-connections]')).toBeNull();
  const collection = screen.getByRole('region', {name:'자료 모으기'});
  expect(within(collection).getAllByRole('listitem')).toHaveLength(4);
  for (const name of ['근로계약서.pdf', '6월_근태기록.pdf', '6월_급여명세서.pdf', '7월_입금내역.png']) expect(within(collection).getByText(name)).toBeVisible();
  await choose('원문 확인');
  expect(document.querySelector('[data-story-documents]')?.children).toHaveLength(3);
  expect(document.querySelector('[data-story-connections]')).toBeInTheDocument();
  expect(screen.getByRole('region', {name:'원문 확인'})).toHaveTextContent('사용자 확인 예시');
  await choose('입금 연결');
  const deposits = screen.getByRole('region', {name:'입금 연결'});
  expect(deposits).toHaveTextContent('1,500,000');
  expect(deposits).toHaveTextContent('500,000');
  expect(deposits).toHaveTextContent('2,000,000');
  expect(document.querySelector('[data-playing]')).toHaveAttribute('data-playing', 'false');
  await choose('차이 확인');
  expect(within(steps).getByRole('button', {name:'차이 확인'})).toHaveAttribute('aria-pressed', 'true');
  expect(document.querySelector('[data-story-documents]')).toBeInTheDocument();
  await choose('자료 모으기');
  expect(document.querySelector('[data-story-documents]')).toBeNull();
});

it('loops automatically, supports replay and freezes the timeline while paused or hidden', () => {
  vi.useFakeTimers();
  vi.stubGlobal('IntersectionObserver', undefined);
  vi.stubGlobal('matchMedia', vi.fn(() => ({matches:false, addEventListener:vi.fn(), removeEventListener:vi.fn()})));
  const view = renderLanding();
  const story = document.querySelector('[data-playing]')!;
  const advance = (ms: number) => act(() => vi.advanceTimersByTime(ms));
  expect(story).toHaveAttribute('data-stage', '0');
  expect(document.querySelector('[data-story-documents]')).toBeNull();
  advance(3700);
  expect(story).toHaveAttribute('data-stage', '1');
  expect(story).toHaveAttribute('data-docking', 'true');
  expect(document.querySelector('[data-story-documents]')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 일시정지'}));
  expect(story).toHaveAttribute('data-layout-playing', 'false');
  advance(10000);
  expect(story).toHaveAttribute('data-stage', '1');
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 재생'}));
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(true);
  fireEvent(document, new Event('visibilitychange'));
  advance(10000);
  expect(story).toHaveAttribute('data-stage', '1');
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
  fireEvent(document, new Event('visibilitychange'));
  advance(3300);
  expect(story).toHaveAttribute('data-stage', '2');
  expect(story).toHaveAttribute('data-docking', 'false');
  advance(3100);
  expect(story).toHaveAttribute('data-stage', '3');
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 일시정지'}));
  advance(20000);
  expect(story).toHaveAttribute('data-stage', '3');
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 재생'}));
  advance(3700);
  expect(story).toHaveAttribute('data-stage', '0');
  expect(story).toHaveAttribute('data-docking', 'false');
  expect(document.querySelector('[data-story-documents]')).toBeNull();
  expect(story).toHaveAttribute('data-playing', 'true');
  for (const [duration, stage] of [[3700, 1], [3300, 2], [3100, 3], [3700, 0]] as const) {
    advance(duration);
    expect(story).toHaveAttribute('data-stage', String(stage));
  }
  advance(3700);
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 다시 보기'}));
  expect(story).toHaveAttribute('data-stage', '0');
  expect(story).toHaveAttribute('data-playing', 'true');
  const steps = screen.getByRole('group', {name:'급여 확인 과정 미리보기'});
  fireEvent.click(within(steps).getByRole('button', {name:'입금 연결'}));
  advance(20000);
  expect(story).toHaveAttribute('data-stage', '2');
  expect(story).toHaveAttribute('data-playing', 'false');
  fireEvent.click(screen.getByRole('button', {name:'애니메이션 재생'}));
  expect(story).toHaveAttribute('data-animate', 'true');
  advance(3100);
  expect(story).toHaveAttribute('data-stage', '3');
  view.unmount();
  expect(vi.getTimerCount()).toBe(0);
  vi.restoreAllMocks();
});

it.each(['en', 'vi', 'zh', 'km'] as const)('renders the new hero and research in %s without Korean fallback', locale => {
  renderLanding(locale);
  expect(screen.getByRole('heading', {level:1})).toHaveTextContent(catalogs[locale].landingEvidence.heroLineTwo);
  const evidence = document.getElementById('why')!;
  expect(evidence).toHaveTextContent(catalogs[locale].landingEvidence.localScope);
  expect(evidence).not.toHaveTextContent(/월급잇다가 필요한 이유|계약서 서명 시 일부만 이해/);
});

it('reveals research on viewport entry once and immediately reveals a keyboard-focused source', () => {
  const observers: {callback: IntersectionObserverCallback; targets: Set<Element>; unobserve: ReturnType<typeof vi.fn>; disconnect: ReturnType<typeof vi.fn>}[] = [];
  vi.stubGlobal('matchMedia', vi.fn(() => ({matches:false, addEventListener:vi.fn(), removeEventListener:vi.fn()})));
  vi.stubGlobal('IntersectionObserver', class {
    targets = new Set<Element>();
    unobserve = vi.fn();
    disconnect = vi.fn();
    constructor(public callback: IntersectionObserverCallback) { observers.push(this); }
    observe(element: Element) { this.targets.add(element); }
  });
  const view = renderLanding();
  const chart = document.querySelector('[data-research="ministry"] figure')!;
  const observer = observers.find(item => item.targets.has(chart))!;
  expect(observer).toBeDefined();
  expect(chart).not.toHaveAttribute('data-entered');
  const notify = (isIntersecting: boolean) => act(() => observer.callback([{target:chart,isIntersecting} as IntersectionObserverEntry], {} as IntersectionObserver));
  notify(false);
  expect(chart).not.toHaveAttribute('data-entered');
  notify(true);
  expect(chart).toHaveAttribute('data-entered', 'true');
  expect(observer.unobserve).toHaveBeenCalledWith(chart);
  notify(false);
  expect(chart).toHaveAttribute('data-entered', 'true');
  const source = within(document.querySelector('[data-research="ministry"]') as HTMLElement).getByRole('link');
  const footer = source.closest('[data-reveal]')!;
  expect(footer).not.toHaveAttribute('data-entered');
  act(() => source.focus());
  expect(source).toHaveFocus();
  expect(footer).toHaveAttribute('data-entered', 'true');
  view.unmount();
  expect(observer.disconnect).toHaveBeenCalled();
});

it.each(['reduced motion', 'no IntersectionObserver'])('keeps research available with %s', mode => {
  if (mode === 'no IntersectionObserver') {
    vi.stubGlobal('IntersectionObserver', undefined);
    vi.stubGlobal('matchMedia', vi.fn(() => ({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()})));
  } else {
    vi.stubGlobal('IntersectionObserver', class { observe() {} disconnect() {} });
  }
  renderLanding();
  const root = document.getElementById('main-content')!.parentElement!;
  expect(root.className).not.toContain('motion-ready');
  expect(screen.getByText('58.4%')).toBeVisible();
  expect(screen.getAllByText('1,548억 원')).toHaveLength(2);
});

it("closes mobile navigation on Escape with focus restored and on anchor selection", async () => {
  const user = userEvent.setup();
  renderLanding();
  const toggle = screen.getByRole("button", { name: "메뉴 열기" });
  await user.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(document.getElementById(toggle.getAttribute("aria-controls")!)).toHaveAttribute("aria-label", "주 메뉴");
  await user.keyboard("{Escape}");
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  expect(toggle).toHaveFocus();
  await user.click(toggle);
  await user.click(screen.getByRole("link", { name: "이용 방법" }));
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  expect(screen.getByRole("link", { name: "이용 방법" })).toHaveAttribute("href", "#how-it-works");
});

it("keeps the native FAQ disclosures operable", async () => {
  const user = userEvent.setup();
  renderLanding();
  const summary = screen.getByText("차이가 나오면 바로 미지급액인가요?");
  expect(summary.tagName).toBe("SUMMARY");
  await user.click(summary);
  expect(summary.closest("details")).toHaveAttribute("open");
  expect(screen.getByText(/아니요. 현재 확인한 자료의 값이 다르다는 뜻/)).toBeVisible();
  await user.click(summary);
  expect(summary.closest("details")).not.toHaveAttribute("open");
});

it("copies the displayed example and announces success", async () => {
  const user = userEvent.setup();
  const write = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
  renderLanding();
  await user.click(screen.getByRole("button", { name: "예시 문장 복사" }));
  expect(write).toHaveBeenCalledWith(screen.getByText(/^6월 급여명세서의 실수령액은/).textContent);
  expect(screen.getByRole("status")).toHaveTextContent("예시 문장을 복사했어요.");
});

it("offers manual copying and focuses the example when clipboard access fails", async () => {
  const user = userEvent.setup();
  vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(new Error("Clipboard unavailable"));
  renderLanding();
  await user.click(screen.getByRole("button", { name: "예시 문장 복사" }));
  expect(screen.getByRole("status")).toHaveTextContent("문장을 직접 선택해서 복사해 주세요.");
  expect(screen.getByText(/^6월 급여명세서의 실수령액은/)).toHaveFocus();
});

it('places the shared language selector inside the existing single header', () => {
  renderLanding();
  const header = screen.getByRole('banner');
  expect(header.querySelectorAll('.language-selector')).toHaveLength(1);
  expect(document.querySelector('.global-language-bar')).toBeNull();
});
