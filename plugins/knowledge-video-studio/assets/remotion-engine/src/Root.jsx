import React from 'react';
import {Composition} from 'remotion';
import {Segment} from './Segment';

const defaults = {
  kind: 'kinetic-title',
  duration: 5,
  fps: 30,
  width: 1920,
  height: 1080,
  title: 'Knowledge Video',
  subtitle: '',
  background: '#101418',
  foreground: '#F4E7C5',
  accent: '#E6573F',
  data: {},
};

export const Root = () => (
  <Composition
    id="KnowledgeSegment"
    component={Segment}
    durationInFrames={150}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={defaults}
    calculateMetadata={({props}) => {
      const fps = Number(props.fps || 30);
      const duration = Number(props.duration || 5);
      return {
        durationInFrames: Math.max(1, Math.round(duration * fps)),
        fps,
        width: Number(props.width || 1920),
        height: Number(props.height || 1080),
        props: {...defaults, ...props},
      };
    }}
  />
);
