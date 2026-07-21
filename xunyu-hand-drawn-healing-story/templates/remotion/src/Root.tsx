import React from "react";
import { Composition } from "remotion";
import { Episode, TOTAL_FRAMES, FPS, WIDTH, HEIGHT } from "./Episode";

export const RemotionRoot: React.FC = () => {
 return (
 <>
 <Composition
 id="Episode"
 component={Episode}
 durationInFrames={TOTAL_FRAMES}
 fps={FPS}
 width={WIDTH}
 height={HEIGHT}
 />
 </>
 );
};
