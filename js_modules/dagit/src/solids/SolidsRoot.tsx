import * as React from "react";
import * as querystring from "query-string";

import Loading from "../Loading";
import { RouteComponentProps } from "react-router";

import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import styled from "styled-components";
import { SolidCard } from "./SolidCard";
import {
  SolidsRootQuery,
  SolidsRootQuery_usedSolids
} from "./types/SolidsRootQuery";
import { SplitPanelChildren } from "../SplitPanelChildren";
import { Colors, NonIdealState } from "@blueprintjs/core";
import { SidebarSolidDefinition } from "../SidebarSolidDefinition";
import SolidTypeSignature from "../SolidTypeSignature";
import {
  SuggestionProvider,
  TokenizingFieldValue,
  tokenizedValuesFromString,
  stringFromValue,
  TokenizingField
} from "../TokenizingField";

function flatUniq(arrs: string[][]) {
  const results: { [key: string]: boolean } = {};
  for (const arr of arrs) {
    for (const item of arr) {
      results[item] = true;
    }
  }
  return Object.keys(results).sort((a, b) => a.localeCompare(b));
}

function searchSuggestionsForSolids(
  solids: SolidsRootQuery_usedSolids[]
): SuggestionProvider[] {
  return [
    {
      token: "name",
      values: () => solids.map(s => s.definition.name)
    },
    {
      token: "pipeline",
      values: () =>
        flatUniq(solids.map(s => s.invocations.map(i => i.pipeline.name)))
    },
    {
      token: "input",
      values: () =>
        flatUniq(
          solids.map(s =>
            s.definition.inputDefinitions.map(d => d.type.displayName)
          )
        )
    },
    {
      token: "output",
      values: () =>
        flatUniq(
          solids.map(s =>
            s.definition.outputDefinitions.map(d => d.type.displayName)
          )
        )
    }
  ];
}

function filterSolidsWithSearch(
  solids: SolidsRootQuery_usedSolids[],
  search: TokenizingFieldValue[]
) {
  return solids.filter(s => {
    for (const item of search) {
      if (
        (item.token === "name" || item.token === undefined) &&
        !s.definition.name.startsWith(item.value)
      ) {
        return false;
      }
      if (
        item.token === "pipeline" &&
        !s.invocations.some(i => i.pipeline.name === item.value)
      ) {
        return false;
      }
      if (
        item.token === "input" &&
        !s.definition.inputDefinitions.some(i =>
          i.type.displayName.startsWith(item.value)
        )
      ) {
        return false;
      }
      if (
        item.token === "output" &&
        !s.definition.outputDefinitions.some(i =>
          i.type.displayName.startsWith(item.value)
        )
      ) {
        return false;
      }
    }
    return true;
  });
}

export const SolidsRoot: React.FunctionComponent<RouteComponentProps> = route => {
  const queryResult = useQuery<SolidsRootQuery>(SOLIDS_ROOT_QUERY);
  return (
    <Loading queryResult={queryResult}>
      {({ usedSolids }) => (
        <SolidsRootWithData usedSolids={usedSolids} route={route} />
      )}
    </Loading>
  );
};

const SolidsRootWithData: React.FunctionComponent<{
  route: RouteComponentProps;
  usedSolids: SolidsRootQuery_usedSolids[];
}> = ({ route: { location, match, history }, usedSolids }) => {
  const { q, typeExplorer } = querystring.parse(location.search);
  const suggestions = searchSuggestionsForSolids(usedSolids);
  const search = tokenizedValuesFromString((q as string) || "", suggestions);
  const filtered = filterSolidsWithSearch(usedSolids, search);
  const selected = usedSolids.find(
    s => s.definition.name === match.params["name"]
  );

  const onSearch = (search: TokenizingFieldValue[]) => {
    history.push({
      search: `?${querystring.stringify({ q: stringFromValue(search) })}`
    });
  };

  const onClickSolid = (defName: string) => {
    history.push(`/solids/${defName}?${querystring.stringify({ q })}`);
  };

  React.useEffect(() => {
    // If the user has typed in a search that brings us to a single result, autoselect it
    if (filtered.length === 1 && (!selected || filtered[0] !== selected)) {
      onClickSolid(filtered[0].definition.name);
    }

    // If the user has clicked a type, translate it into a search
    if (typeof typeExplorer === "string") {
      onSearch([...search, { token: "input", value: typeExplorer }]);
    }
  });

  return (
    <Wrapper>
      <SplitPanelChildren
        identifier={"solids"}
        leftInitialPercent={40}
        leftMinWidth={420}
        left={
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              height: "100%"
            }}
          >
            <div
              style={{
                padding: "15px 10px",
                borderBottom: `1px solid ${Colors.LIGHT_GRAY2}`
              }}
            >
              <TokenizingField
                values={search}
                onChange={search => onSearch(search)}
                suggestionProviders={suggestions}
                placeholder={"Filter by name or input/output type..."}
              />
            </div>
            <SolidListScrollContainer>
              {filtered
                .sort((a, b) =>
                  a.definition.name.localeCompare(b.definition.name)
                )
                .map(s => (
                  <SolidListItem
                    key={s.definition.name}
                    selected={s === selected}
                    onClick={() => onClickSolid(s.definition.name)}
                  >
                    <SolidName>{s.definition.name}</SolidName>
                    <SolidTypeSignature definition={s.definition} />
                  </SolidListItem>
                ))}
            </SolidListScrollContainer>
          </div>
        }
        right={
          selected ? (
            <SolidDetailScrollContainer>
              <SolidCard definition={selected.definition} />
              <SidebarSolidDefinition
                definition={selected.definition}
                showingSubsolids={false}
                onClickInvocation={({ pipelineName, handleID }) =>
                  history.push(
                    `/p/${pipelineName}/explore/${handleID
                      .split(".")
                      .join("/")}`
                  )
                }
                definitionInvocations={selected.invocations.map(i => ({
                  handleID: i.solidHandle.handleID,
                  pipelineName: i.pipeline.name
                }))}
              />
            </SolidDetailScrollContainer>
          ) : (
            <NonIdealState
              title="No solid selected"
              description="Select a solid to see its definition and invocations."
            />
          )
        }
      />
    </Wrapper>
  );
};

export const SOLIDS_ROOT_QUERY = gql`
  query SolidsRootQuery {
    usedSolids {
      __typename
      definition {
        ...SolidCardSolidDefinitionFragment
        ...SidebarSolidDefinitionFragment
      }
      invocations {
        __typename
        pipeline {
          name
        }
        solidHandle {
          handleID
        }
      }
    }
  }

  ${SolidCard.fragments.SolidCardSolidDefinitionFragment}
  ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
`;

const SolidListItem = styled.div<{ selected: boolean }>`
  background: ${({ selected }) => (selected ? Colors.BLUE3 : Colors.WHITE)};
  color: ${({ selected }) => (selected ? Colors.WHITE : Colors.DARK_GRAY3)};
  font-size: 14px;
  display: flex;
  flex-direction: column;
  padding: 10px 15px;
  user-select: none;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  & > code.bp3-code {
    color: ${({ selected }) => (selected ? Colors.WHITE : Colors.DARK_GRAY3)};
    background: transparent;
    padding: 5px 0 0 0;
  }
`;

const SolidListScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;

const SolidDetailScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;

const SolidName = styled.div`
  flex: 1;
  font-weight: 600;
`;

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  position: absolute;
  padding-top: 50px;
  top: 0;
`;
