import React from "react";
import {
 AbsoluteFill,
 Img,
 interpolate,
 Sequence,
 staticFile,
 useCurrentFrame,
 Easing,
} from "remotion";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

/** 编辑分镜；public/ 放 NN-bw.png / NN-color.png（实体文件） */
const SHOTS = [
 { id: 1, dur: 5, text: "第一句旁白。" },
 { id: 2, dur: 5, text: "第二句旁白。" },
 { id: 3, dur: 5, text: "第三句旁白。\n可两行。" },
] as const;

export const TOTAL_FRAMES = SHOTS.reduce((s, x) => s + x.dur * FPS, 0);

const pad = (n: number) => String(n).padStart(2, "0");

const Shot: React.FC<{
 id: number;
 text: string;
 durationInFrames: number;
 isLast: boolean;
}> = ({ id, text, durationInFrames, isLast }) => {
 const frame = useCurrentFrame();
 const wipeFrames = Math.round(1.0 * FPS);
 const colorFrames = Math.round(0.8 * FPS);
 const captionFrames = Math.round(0.45 * FPS);

 const wipe = interpolate(frame, [0, wipeFrames], [0, 100], {
 extrapolateLeft: "clamp",
 extrapolateRight: "clamp",
 easing: Easing.out(Easing.cubic),
 });

 const colorStart = Math.round(wipeFrames * 0.85);
 const colorOp = interpolate(
 frame,
 [colorStart, colorStart + colorFrames],
 [0, 1],
 {
 extrapolateLeft: "clamp",
 extrapolateRight: "clamp",
 easing: Easing.out(Easing.cubic),
 }
 );

 const captionOp = interpolate(
 frame,
 [Math.round(0.15 * FPS), Math.round(0.15 * FPS) + captionFrames],
 [0, 1],
 {
 extrapolateLeft: "clamp",
 extrapolateRight: "clamp",
 easing: Easing.out(Easing.cubic),
 }
 );

 const zoom = interpolate(frame, [0, durationInFrames], [1, 1.04], {
 extrapolateLeft: "clamp",
 extrapolateRight: "clamp",
 });

 const fadeOut = isLast
 ? interpolate(
 frame,
 [durationInFrames - Math.round(0.4 * FPS), durationInFrames],
 [0, 1],
 { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
 )
 : 0;

 return (
 <AbsoluteFill style={{ backgroundColor: "#fff" }}>
 <AbsoluteFill
 style={{
 transform: `scale(${zoom})`,
 transformOrigin: "center 55%",
 WebkitMaskImage: `linear-gradient(90deg, #000 0%, #000 ${wipe}%, transparent ${wipe}%)`,
 maskImage: `linear-gradient(90deg, #000 0%, #000 ${wipe}%, transparent ${wipe}%)`,
 }}
 >
 <Img
 src={staticFile(`${pad(id)}-bw.png`)}
 style={{
 position: "absolute",
 inset: 0,
 width: "100%",
 height: "100%",
 objectFit: "cover",
 }}
 />
 <Img
 src={staticFile(`${pad(id)}-color.png`)}
 style={{
 position: "absolute",
 inset: 0,
 width: "100%",
 height: "100%",
 objectFit: "cover",
 opacity: colorOp,
 }}
 />
 </AbsoluteFill>

 <div
 style={{
 position: "absolute",
 top: "6.5%",
 left: "7%",
 right: "7%",
 textAlign: "center",
 fontFamily: '"Kaiti SC", "STKaiti", "Songti SC", serif',
 fontSize: 42,
 lineHeight: 1.55,
 letterSpacing: "0.04em",
 color: "#222",
 opacity: captionOp,
 whiteSpace: "pre-line",
 textShadow: "0 0 12px #fff, 0 0 4px #fff",
 }}
 >
 {text}
 </div>

 {fadeOut > 0 ? (
 <AbsoluteFill style={{ backgroundColor: "#fff", opacity: fadeOut }} />
 ) : null}
 </AbsoluteFill>
 );
};

export const Episode: React.FC = () => {
 let from = 0;
 return (
 <AbsoluteFill style={{ backgroundColor: "#fff" }}>
 {SHOTS.map((shot, i) => {
 const durationInFrames = shot.dur * FPS;
 const seq = (
 <Sequence key={shot.id} from={from} durationInFrames={durationInFrames}>
 <Shot
 id={shot.id}
 text={shot.text}
 durationInFrames={durationInFrames}
 isLast={i === SHOTS.length - 1}
 />
 </Sequence>
 );
 from += durationInFrames;
 return seq;
 })}
 </AbsoluteFill>
 );
};
