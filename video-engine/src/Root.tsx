import React from "react";
import { Composition, Sequence, Audio, staticFile } from "remotion";
import { SceneRenderer, SceneData } from "./SceneRenderer";

export const FPS = 30;

export interface SyncedSceneData extends SceneData {
  audio_src?: string | null;
}

export const MainVideo: React.FC<{ scenes: SyncedSceneData[] }> = ({ scenes = [] }) => {
  return (
    <>
      {scenes.map((scene) => {
        const startFrame = Math.round(scene.start_time * FPS);
        const durationInFrames = Math.max(
          FPS,
          Math.round((scene.end_time - scene.start_time) * FPS)
        );

        return (
          <Sequence
            key={scene.scene_id}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            <SceneRenderer scene={scene} />
            {scene.audio_src && (
              <Audio src={staticFile(scene.audio_src)} />
            )}
          </Sequence>
        );
      })}
    </>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CourseLessonVideo"
      component={MainVideo as React.ComponentType<{ scenes: SyncedSceneData[] }>}
      durationInFrames={1500} 
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{
        scenes: [] as SyncedSceneData[], 
      }}
      calculateMetadata={({ props }) => {
        const scenes = (props.scenes as SyncedSceneData[]) || []; 
        const lastScene = scenes[scenes.length - 1];
        
        // Find the exact end time, default to 50s if none exists
        const totalDurationSec = lastScene ? lastScene.end_time : 50;
        const dynamicDuration = Math.max(FPS, Math.ceil(totalDurationSec * FPS));
        
        return {
          durationInFrames: dynamicDuration,
          props, // Passes the JSON payload back to the renderer
        };
      }}
    />
  );
};