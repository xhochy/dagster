import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import SVGViewport, { DETAIL_ZOOM, SVGViewportInteractor } from "./SVGViewport";
import { SolidNameOrPath } from "../PipelineExplorer";
import SolidNode from "./SolidNode";
import { IFullPipelineLayout, IFullSolidLayout } from "./getFullSolidLayout";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";
import { SolidLinks } from "./SolidLinks";
import { Edge, isHighlighted, isSolidHighlighted } from "./highlighting";
import { ParentSolidNode, SVGLabeledParentRect } from "./ParentSolidNode";

const NoOp = () => {};

interface IPipelineGraphProps {
  pipelineName: string;
  backgroundColor: string;
  layout: IFullPipelineLayout;
  solids: PipelineGraphSolidFragment[];
  parentHandleID?: string;
  parentSolid?: PipelineGraphSolidFragment;
  selectedHandleID?: string;
  selectedSolid?: PipelineGraphSolidFragment;
  highlightedSolids: Array<PipelineGraphSolidFragment>;
  interactor?: SVGViewportInteractor;
  onClickSolid?: (arg: SolidNameOrPath) => void;
  onDoubleClickSolid?: (arg: SolidNameOrPath) => void;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

interface IPipelineContentsState {
  highlighted: Edge[];
}

export class PipelineGraphContents extends React.PureComponent<
  IPipelineContentsProps,
  IPipelineContentsState
> {
  state: IPipelineContentsState = {
    highlighted: []
  };

  onHighlightEdges = (highlighted: Edge[]) => {
    this.setState({ highlighted });
  };

  render() {
    const {
      layout,
      minified,
      solids,
      parentSolid,
      parentHandleID,
      onClickSolid = NoOp,
      onDoubleClickSolid = NoOp,
      onEnterCompositeSolid = NoOp,
      highlightedSolids,
      selectedSolid,
      selectedHandleID
    } = this.props;

    return (
      <>
        {parentSolid && layout.parent && (
          <SVGLabeledParentRect
            {...layout.parent.invocationBoundingBox}
            key={`composite-rect-${parentHandleID}`}
            label={parentSolid.name}
            fill={Colors.LIGHT_GRAY5}
            minified={minified}
          />
        )}
        {selectedSolid && (
          // this rect is hidden beneath the user's selection with a React key so that
          // when they expand the composite solid React sees this component becoming
          // the one above and re-uses the DOM node. This allows us to animate the rect's
          // bounds from the parent layout to the inner layout with no React state.
          <SVGLabeledParentRect
            {...layout.solids[selectedSolid.name].solid}
            key={`composite-rect-${selectedHandleID}`}
            label={""}
            fill={Colors.LIGHT_GRAY5}
            minified={true}
          />
        )}

        {parentSolid && (
          <ParentSolidNode
            onClickSolid={onClickSolid}
            onDoubleClick={name => onDoubleClickSolid({ name })}
            onHighlightEdges={this.onHighlightEdges}
            highlightedEdges={this.state.highlighted}
            key={`composite-rect-${parentHandleID}-definition`}
            minified={minified}
            solid={parentSolid}
            layout={layout}
          />
        )}
        <SolidLinks
          layout={layout}
          opacity={0.2}
          connections={layout.connections}
          onHighlight={this.onHighlightEdges}
        />
        <SolidLinks
          layout={layout}
          opacity={0.55}
          onHighlight={this.onHighlightEdges}
          connections={layout.connections.filter(({ from, to }) =>
            isHighlighted(this.state.highlighted, {
              a: from.solidName,
              b: to.solidName
            })
          )}
        />
        {solids.map(solid => (
          <SolidNode
            key={solid.name}
            invocation={solid}
            definition={solid.definition}
            minified={minified}
            onClick={() => onClickSolid({ name: solid.name })}
            onDoubleClick={() => onDoubleClickSolid({ name: solid.name })}
            onEnterComposite={() => onEnterCompositeSolid({ name: solid.name })}
            onHighlightEdges={this.onHighlightEdges}
            layout={layout.solids[solid.name]}
            selected={selectedSolid === solid}
            highlightedEdges={
              isSolidHighlighted(this.state.highlighted, solid.name)
                ? this.state.highlighted
                : EmptyHighlightedArray
            }
            dim={
              highlightedSolids.length > 0 &&
              highlightedSolids.indexOf(solid) === -1
            }
          />
        ))}
      </>
    );
  }
}

// This is a specific empty array we pass to represent the common / empty case
// so that SolidNode can use shallow equality comparisons in shouldComponentUpdate.
const EmptyHighlightedArray: never[] = [];

export default class PipelineGraph extends React.Component<
  IPipelineGraphProps
> {
  static fragments = {
    PipelineGraphSolidFragment: gql`
      fragment PipelineGraphSolidFragment on Solid {
        name
        ...SolidNodeInvocationFragment
        definition {
          name
          ...SolidNodeDefinitionFragment
        }
      }

      ${SolidNode.fragments.SolidNodeInvocationFragment}
      ${SolidNode.fragments.SolidNodeDefinitionFragment}
    `
  };

  viewportEl: React.RefObject<SVGViewport> = React.createRef();

  focusOnSolid = (arg: SolidNameOrPath) => {
    const lastName = "name" in arg ? arg.name : arg.path[arg.path.length - 1];
    const solidLayout = this.props.layout.solids[lastName];
    if (!solidLayout) {
      return;
    }
    const cx = solidLayout.boundingBox.x + solidLayout.boundingBox.width / 2;
    const cy = solidLayout.boundingBox.y + solidLayout.boundingBox.height / 2;

    this.viewportEl.current!.smoothZoomToSVGCoords(cx, cy, DETAIL_ZOOM);
  };

  closestSolidInDirection = (dir: string): string | undefined => {
    const { layout, selectedSolid } = this.props;
    if (!selectedSolid) return;

    const current = layout.solids[selectedSolid.name];
    const center = (solid: IFullSolidLayout): { x: number; y: number } => ({
      x: solid.boundingBox.x + solid.boundingBox.width / 2,
      y: solid.boundingBox.y + solid.boundingBox.height / 2
    });

    /* Sort all the solids in the graph based on their attractiveness
    as a jump target. We want the nearest node in the exact same row for left/right,
    and the visually "closest" node above/below for up/down. */
    const score = (solid: IFullSolidLayout): number => {
      const dx = center(solid).x - center(current).x;
      const dy = center(solid).y - center(current).y;

      if (dir === "left" && dy === 0 && dx < 0) {
        return -dx;
      }
      if (dir === "right" && dy === 0 && dx > 0) {
        return dx;
      }
      if (dir === "up" && dy < 0) {
        return -dy + Math.abs(dx) / 5;
      }
      if (dir === "down" && dy > 0) {
        return dy + Math.abs(dx) / 5;
      }
      return Number.NaN;
    };

    const closest = Object.keys(layout.solids)
      .map(name => ({ name, score: score(layout.solids[name]) }))
      .filter(e => e.name !== selectedSolid.name && !Number.isNaN(e.score))
      .sort((a, b) => b.score - a.score)
      .pop();

    return closest ? closest.name : undefined;
  };

  onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).nodeName === "INPUT") return;

    const dir = { 37: "left", 38: "up", 39: "right", 40: "down" }[e.keyCode];
    if (!dir) return;

    const nextSolid = this.closestSolidInDirection(dir);
    if (nextSolid && this.props.onClickSolid) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClickSolid({ name: nextSolid });
    }
  };

  unfocus = (e: React.MouseEvent<any>) => {
    this.viewportEl.current!.autocenter(true);
    e.stopPropagation();
  };

  unfocusOutsideContainer = (e: React.MouseEvent<any>) => {
    if (this.props.parentSolid && this.props.onLeaveCompositeSolid) {
      this.props.onLeaveCompositeSolid();
    } else {
      this.unfocus(e);
    }
  };

  componentDidUpdate(prevProps: IPipelineGraphProps) {
    if (prevProps.parentSolid !== this.props.parentSolid) {
      this.viewportEl.current!.autocenter();
    }
  }

  render() {
    const {
      layout,
      interactor,
      pipelineName,
      backgroundColor,
      onClickBackground,
      onDoubleClickSolid
    } = this.props;

    return (
      <SVGViewport
        ref={this.viewportEl}
        key={pipelineName}
        interactor={interactor || SVGViewport.Interactors.PanAndZoom}
        backgroundColor={backgroundColor}
        graphWidth={layout.width}
        graphHeight={layout.height}
        onKeyDown={this.onKeyDown}
        onDoubleClick={this.unfocusOutsideContainer}
      >
        {({ scale }: any) => (
          <SVGContainer
            width={layout.width}
            height={layout.height + 200}
            onClick={onClickBackground}
            onDoubleClick={this.unfocus}
          >
            <PipelineGraphContents
              layout={layout}
              minified={scale < DETAIL_ZOOM - 0.01}
              onDoubleClickSolid={onDoubleClickSolid || this.focusOnSolid}
              {...this.props}
            />
          </SVGContainer>
        )}
      </SVGViewport>
    );
  }
}

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
