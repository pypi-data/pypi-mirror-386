import pandas as pd
import numpy as np
import holoviews as hv
import panel as pn

from pathlib import Path

import param

from .utils import sparse_column_value_counts, vertical_bar_html
from .process_data import load_data
from .ui_helpers import HTMLRadioIconGroup
from .archetypes import make_matchup_matrix
from .html_vis import make_combined_matchup_html, make_card_stack

pn.extension(
    'tabulator', 
    sizing_mode="stretch_width", 
    throttled=True, 
    js_files={'hover': 'hover.js'},
)
hv.extension('bokeh')

from scipy import sparse
from scipy.stats import binomtest

class MTGAnalyzer(param.Parameterized):
    """Holds all of the data and filters, serves up vis.

    This object holds the loaded data and manages selections.
    It has various ui methods, which each return a display based on
    the data and filters.
    """
    date_range = param.DateRange(default=None, doc="Date range for analysis")

    selected_cards = param.List(default=[], doc="Cards required in deck")
    excluded_cards = param.List(default=[], doc="Cards excluded from deck")

    valid_rows = param.Array(default=np.array([]), doc="Selected indices")
    valid_wr_rows = param.Array(default=np.array([]), doc="Selected indices with valid wr")
    valid_match_rows = param.Array(default=np.array([]), doc="Selected match indices")

    selected_archetype = param.String(default=None, allow_None=True, doc="Selected archetype")

    selected_analyze_card = param.List(default=[], doc="Cards to analyze in detail")

    df_winrates = param.DataFrame(doc="Matchup matrix win rates")
    
    def __init__(self, df, res_df, card_vectors, vocabulary, oracleid_lookup, cards_data, cluster_map, clusters_id, archetype_list, **params):
        super().__init__(**params)
        self.df = df
        self.res_df = res_df
        self.X = card_vectors
        self.feature_names = vocabulary
        self.oracleid_lookup = oracleid_lookup
        self.cards_data = cards_data
        self.cluster_map = cluster_map
        self.clusters_id = clusters_id
        self.archetype_list = archetype_list
        
        self._initialize_card_list()
        self.find_valid_rows()
        self.set_archetypes()
        
    def _initialize_card_list(self):
        # Get unique cards from feature names, removing _SB suffix
        self.card_options = sorted(list(set(
            [name.replace('_SB', '') for name in self.feature_names.keys()]
        )))

    @property
    def date_filter(self):
        if self.date_range is not None:
            return (self.df['Date'] >= self.date_range[0]) & (self.df['Date'] <= self.date_range[1])
        else:
            # Needs to broadcast with other filters.
            #
            return True
        
    @property
    def match_date_filter(self):
        if self.date_range is not None:
            return (self.res_df['Date'] >= self.date_range[0]) & (self.res_df['Date'] <= self.date_range[1])
        else:
            # Never broadcast with other filters.
            #
            return np.ones(self.res_df.shape[0])
    
    @property
    def contents_filter(self):
        """
        Find row indices where specified logical combinations of cards are present.
        """

        row_mask = np.ones(self.X.shape[0], dtype=bool)
        
        # We need to handle things a bit awkwardly here to account for cards being in either main or sideboard.
        # This is because each card when present in the sideboard is stored as {CARD}_SB.
        #

        for pair_idx, pair in enumerate(
            [(self.feature_names.get(c), self.feature_names.get(f"{c}_SB")) for c in self.selected_cards]
        ):
            # Check pair format
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError(f"Each pair must be a tuple/list of length 2. Error in pair {pair_idx}: {pair}")
            
            col1, col2 = pair
            pair_rows = set()
            
            # Handle col1
            if col1 is not None:
                if not isinstance(col1, (int, np.integer)):
                    raise TypeError(f"Column index must be integer or None. Got {type(col1)} for column 1 in pair {pair_idx}")
                if col1 < 0 or col1 >= self.X.shape[1]:
                    raise ValueError(f"Column index {col1} out of bounds for matrix with {self.X.shape[1]} columns")
                pair_rows.update(self.X.getcol(col1).nonzero()[0])
                
            # Handle col2
            if col2 is not None:
                if not isinstance(col2, (int, np.integer)):
                    raise TypeError(f"Column index must be integer or None. Got {type(col2)} for column 2 in pair {pair_idx}")
                if col2 < 0 or col2 >= self.X.shape[1]:
                    raise ValueError(f"Column index {col2} out of bounds for matrix with {self.X.shape[1]} columns")
                pair_rows.update(self.X.getcol(col2).nonzero()[0])
            
            # If both columns in a pair are None, skip this pair
            if col1 is None and col2 is None:
                continue
                
            # Create mask for current pair
            current_mask = np.zeros(self.X.shape[0], dtype=bool)
            current_mask[list(pair_rows)] = True
            
            # Update overall mask (AND condition)
            row_mask &= current_mask
            
        for pair_idx, pair in enumerate(
            [(self.feature_names.get(c), self.feature_names.get(f"{c}_SB")) for c in self.excluded_cards]
        ):
            # Check pair format
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError(f"Each pair must be a tuple/list of length 2. Error in pair {pair_idx}: {pair}")
            
            col1, col2 = pair
            pair_rows = set()
            
            # Handle col1
            if col1 is not None:
                if not isinstance(col1, (int, np.integer)):
                    raise TypeError(f"Column index must be integer or None. Got {type(col1)} for column 1 in pair {pair_idx}")
                if col1 < 0 or col1 >= self.X.shape[1]:
                    raise ValueError(f"Column index {col1} out of bounds for matrix with {self.X.shape[1]} columns")
                pair_rows.update(self.X.getcol(col1).nonzero()[0])
                
            # Handle col2
            if col2 is not None:
                if not isinstance(col2, (int, np.integer)):
                    raise TypeError(f"Column index must be integer or None. Got {type(col2)} for column 2 in pair {pair_idx}")
                if col2 < 0 or col2 >= self.X.shape[1]:
                    raise ValueError(f"Column index {col2} out of bounds for matrix with {self.X.shape[1]} columns")
                pair_rows.update(self.X.getcol(col2).nonzero()[0])
            
            # If both columns in a pair are None, skip this pair
            if col1 is None and col2 is None:
                continue
                
            # Create mask for current pair
            current_mask = np.zeros(self.X.shape[0], dtype=bool)
            current_mask[list(pair_rows)] = True
            
            # Update overall mask (AND condition)
            row_mask &= ~current_mask
        
        return row_mask

    @property
    def archetype_filter(self):
        if self.selected_archetype is not None:
            return self.df['Archetype'] == self.selected_archetype
        else:
            return True

    def card_name_formatter(self, card_name):
        # Return HTML with data attribute for the image URL
        #
        return f"""<hover-card oracleId="{self.oracleid_lookup.get(card_name)}">{card_name}</hover-card><br>"""
    
    @param.depends('date_range', 'selected_cards', 'excluded_cards', 'selected_archetype', watch=True)
    def find_valid_rows(self):
        """
        Find row indices where specified logical combinations of cards are present.
        """

        # print(f'{self.date_range=}, {self.selected_cards=}, {self.excluded_cards=}, {self.selected_archetype=}')
        row_mask = self.date_filter & self.contents_filter & self.archetype_filter
        
        # Return row indices that satisfy all conditions
        self.valid_rows = np.where(row_mask)[0]
        self.valid_wr_rows = np.where(row_mask & ~self.df['Invalid_WR'])[0]

        self.valid_match_rows = np.where(self.match_date_filter)[0]

    @param.depends('valid_match_rows', watch=True)
    def set_archetypes(self):
        # print(f'{self.res_df=}')
        # print(f'{self.res_df.loc[self.valid_match_rows]=}')
        # print(f'{self.archetype_list=}')
        # print(f'{pd.Series(self.archetype_list).loc[self.valid_match_rows].to_list()=}')
        self.ci_data, self.df_winrates, self.df_wr_lower, self.df_wr_upper = make_matchup_matrix(
            self.df, 
            self.res_df.loc[self.valid_match_rows], 
            self.cluster_map, 
            self.clusters_id, 
            self.archetype_list,
        )
        if self.date_range is not None:
            archetypes = self.df.loc[self.date_filter]['Archetype']
        else:
            archetypes = self.df['Archetype']
        self.meta_share = {
            self.cluster_map[k]: v*100 for k,v in (
                archetypes.value_counts()/archetypes.shape[0]
            ).to_dict().items()
        }

    @param.depends('valid_wr_rows')
    def get_selection_info(self):
        return pn.Row(
            pn.pane.Markdown(
                f'You are currently looking at {self.valid_rows.shape[0]} decks, {self.valid_wr_rows.shape[0]} of which have valid win rate information.',
                width=200,
                margin=4,
            ),
            pn.widgets.TooltipIcon(
                value="""
League data and other sources only show decks with 100% winrate, so they can't be included in win rate calculations. They still contribute to aggregation info.

To change your filter, you can do any of the following:
- Select cards that are required in the 75
- Select cards that cannot be in the 75
- Select an aggregated archetype

Each filter stacks - use the "Reset filter" button on the left to clear selections.
""",
                max_width=10
            ),
            sizing_mode='fixed',
        )

    @param.depends('valid_wr_rows')
    def get_deck_view(self):
        valid_cards = np.unique(self.X[self.valid_rows].nonzero()[1])
        # if valid_cards.shape[0] > 500:
        #     return pn.pane.Markdown(
        #         f'''Too many cards to display deck aggregation. Make a more restrictive filter.
        #         Current cards: {valid_cards.shape[0]}, Max cards: 500
        #         '''
        #     )
        
        # Work out how many of each card is played in aggregate.
        #
        counts_df = pd.DataFrame(
            sparse_column_value_counts(
                self.X[self.valid_rows][:, valid_cards]
            )
        ).fillna(0)

        # Index properly by card name.
        #
        idx_card_map = {v: k for k, v in self.feature_names.items()}
        counts_df.index = [idx_card_map.get(c) for c in valid_cards]
        counts_df.index.name = 'Card'

        # Handle for when we have more than 4 of a card.
        # We should be able to aggregate to 4+ without losing value.
        # Mono color standard or limited decks are the only real issue here, where basics show up >4x.
        #
        if any(counts_df.columns>4):
            counts_df['4+'] = np.nansum(counts_df[[col for col in counts_df.columns if col>=4]], axis=1)
            counts_df = counts_df.rename(columns={0:'0',1:'1',2:'2',3:'3'})
            col_list = ['0','1','2','3','4+']
            
        else:
            counts_df = counts_df.rename(columns={0:'0',1:'1',2:'2',3:'3',4:'4'})
            col_list = ['0','1','2','3','4']

        for col in col_list:
            if col not in counts_df.columns:
                counts_df[col] = 0

        counts_df = counts_df[col_list]
        counts_df.fillna(0)

        # Split into main/sb.
        #
        mb_counts_df = counts_df.loc[
            [i for i in counts_df.index if not i.endswith('_SB')]
        ].sort_values(
            col_list
        )

        sb_counts_df = counts_df.loc[
            [i for i in counts_df.index if i.endswith('_SB')]
        ].sort_values(
            col_list
        )

        # Remove the _SB suffix
        #
        sb_counts_df.index = [c[:-3] for c in sb_counts_df.index]
        sb_counts_df.index.name = 'Card'

        # Preprocess DataFrame to apply HTML formatter
        #
        for col in col_list:
            mb_counts_df[col] = mb_counts_df[col].apply(vertical_bar_html)
            sb_counts_df[col] = sb_counts_df[col].apply(vertical_bar_html)

        # Create tabulator with HTML formatter.
        # First do all of the qtty columns.
        #
        formatters = {
            col: {'type': 'html'} for col in col_list
        }

        # Then do the name column.
        formatters['Card'] = {'type': 'html'}

        mb_counts_df = mb_counts_df.reset_index()
        mb_counts_df['Card'] = mb_counts_df['Card'].apply(self.card_name_formatter)
        sb_counts_df = sb_counts_df.reset_index()
        sb_counts_df['Card'] = sb_counts_df['Card'].apply(self.card_name_formatter)

        mb_table = pn.widgets.Tabulator(
            mb_counts_df, 
            formatters=formatters, 
            pagination='local', 
            show_index=False,
            disabled=True,
            sizing_mode='stretch_both',
            widths={'Card': 150,},# '0': 50, '1': 50, '2': 50, '3': 50, '4+': 50,}
        )
        sb_table = pn.widgets.Tabulator(
            sb_counts_df, 
            formatters=formatters, 
            pagination='local', 
            show_index=False,
            disabled=True,
            sizing_mode='stretch_both',
            widths={'Col A': 100, 'Col B': 150, 'Col C': 80}
        )
    
        return pn.Row(
            pn.Column(
                pn.pane.HTML('<h3>Main</h3>'),
                mb_table,
                sizing_mode='stretch_both',
            ), 
            pn.Column(
                pn.pane.HTML('<h3>Sideboard</h3>'),
                sb_table,
                sizing_mode='stretch_both',
            ),
        )
     
    @param.depends('selected_analyze_card', 'valid_rows')
    def get_card_analysis(self):
        """Analyse the prevalence of a specific card, quantity distribution."""

        if not self.selected_analyze_card:
            return pn.pane.Markdown("Select a card to see analysis")
        
        display = list()
            
        for card in self.selected_analyze_card:
            mb_idx = self.feature_names.get(card)
            sb_idx = self.feature_names.get(f"{card}_SB")
            
            if (mb_idx is None) and (sb_idx is None):
                return pn.pane.Markdown("Card not found in dataset")
            
            # We need to handle for when the card shows up just in sb/mb/both.
            #
            if mb_idx is None:
                mb_copies = []
                _, _, sb_copies = sparse.find(self.X[self.valid_rows][:, sb_idx])
                n_decks = sb_copies.shape[0]
            elif sb_idx is None:
                sb_copies = []
                _, _, mb_copies = sparse.find(self.X[self.valid_rows][:, mb_idx])
                n_decks = mb_copies.shape[0]
            else:
                mb_d, _ = self.X[self.valid_rows][:, mb_idx].nonzero()
                sb_d, _ = self.X[self.valid_rows][:, sb_idx].nonzero()
                d = set(np.concatenate([mb_d, sb_d]))
                mb_copies = self.X[self.valid_rows][list(d), mb_idx].toarray().flatten()
                sb_copies = self.X[self.valid_rows][list(d), sb_idx].toarray().flatten()
                n_decks = len(d)

            max_mb_copies=np.nanmax(mb_copies) if len(mb_copies) else 0
            max_sb_copies=np.nanmax(sb_copies) if len(sb_copies) else 0
            bins = np.arange(-0.5, np.nanmax([max_mb_copies, max_sb_copies, 5]), 1)
            # mb_y, _ = np.histogram(mb_copies, bins, density=True)
            # sb_y, _ = np.histogram(sb_copies, bins, density=True)

            mb_y, _ = np.histogram(mb_copies, bins)
            mb_y[0] += self.valid_rows.shape[0] - n_decks
            mb_y = mb_y / mb_y.sum()

            sb_y, _ = np.histogram(sb_copies, bins)
            sb_y[0] += self.valid_rows.shape[0] - n_decks
            sb_y = sb_y / sb_y.sum()

            display.append(hv.Bars(
                pd.DataFrame({
                    'Frequency': np.concatenate([mb_y, sb_y]),
                    'Qtty': [0,1,2,3,4,0,1,2,3,4],
                    'Board': ['M']*5 + ['SB'] * 5,
                    # 'B': ['Main'] * 5 + ['Sideboard'] * 5
                }),
                kdims=['Qtty', 'Board'],
            ).opts(
                width=375,
                height=375,
                title=f"Frequency: {card}",
                toolbar=None, 
                default_tools=[],
                active_tools=[],
            ))
        return hv.Layout(display).cols(1)
    
    @param.depends('selected_analyze_card', 'valid_wr_rows')
    def get_winrate_analysis(self):
        """Perform card quantity based win rate analysis.
        Error bars are confidence interval on the binomial test.
        """

        if not self.selected_analyze_card:
            return pn.pane.Markdown("Select a card to see win rate analysis")
            
        display = list()

        for card in self.selected_analyze_card:
            # Calculate win rates by copy count
            
            if not card in self.feature_names and not f'{card}_SB' in self.feature_names:
                display.append(pn.pane.Markdown("Card not found in dataset"))
            
            plots = list()

            # Handle differently if the card doesn't show up in main/side.
            #
            
            mb_idx = self.feature_names.get(card)
            mb_win_rates = []
            if mb_idx is not None:    
                copy_counts = self.X[self.valid_wr_rows][:, mb_idx].toarray()

                # print(self.df.loc[self.valid_wr_rows,['Wins']].value_counts(), copy_counts)
                
                
                for i in range(5):  # 0-4 copies
                    mask = copy_counts == i
                    wins = self.df.loc[self.valid_wr_rows].reset_index().loc[mask.ravel(), 'Wins'].sum()
                    total = wins + self.df.loc[self.valid_wr_rows].reset_index().loc[mask.ravel(), 'Losses'].sum()
                    if total:
                        ci = binomtest(k=int(wins), n=int(total)).proportion_ci()
                        winrate = wins/total if total else np.nan
                        mb_win_rates.append({
                            'copies': i-0.1, 
                            'winrate': winrate,
                            'errmin': winrate - ci.low,
                            'errmax': ci.high - winrate,
                        })
                    else:
                        # For completeness
                        #
                        mb_win_rates.append({
                            'copies': i-0.1, 
                            'winrate': np.nan,
                            'errmin': np.nan,
                            'errmax': np.nan,
                        })
                
            plots.append(hv.Scatter(
                mb_win_rates, 'copies', 'winrate', label='Main',
            ).opts(size=7,))
            plots.append(hv.ErrorBars(
                mb_win_rates, 'copies', vdims=['winrate', 'errmin', 'errmax'],
            ))

            sb_idx = self.feature_names.get(f'{card}_SB')
            sb_win_rates = []
            if sb_idx is not None:    
                copy_counts = self.X[self.valid_wr_rows][:, sb_idx].toarray()
                
                
                for i in range(5):  # 0-4 copies
                    mask = copy_counts == i
                    wins = self.df.loc[self.valid_wr_rows].reset_index().loc[mask.ravel(), 'Wins'].sum()
                    total = wins + self.df.loc[self.valid_wr_rows].reset_index().loc[mask.ravel(), 'Losses'].sum()

                    if total:
                        ci = binomtest(k=int(wins), n=int(total)).proportion_ci()
                        winrate = wins/total if total else np.nan
                        sb_win_rates.append({
                            'copies': i+0.1, 
                            'winrate': winrate,
                            'errmin': winrate - ci.low,
                            'errmax': ci.high - winrate,
                        })
                    else:
                        # For completeness
                        #
                        sb_win_rates.append({
                            'copies': i+0.1, 
                            'winrate': np.nan,
                            'errmin': np.nan,
                            'errmax': np.nan,
                        })
                
            plots.append(hv.Scatter(
                sb_win_rates, 'copies', 'winrate', label='SB',
            ).opts(size=7, toolbar=None, default_tools=[],))
            plots.append(hv.ErrorBars(
                sb_win_rates, 'copies', vdims=['winrate', 'errmin', 'errmax'],
            ).opts(toolbar=None, default_tools=[],))

            # Add helper lines for context, 50% and the average wr of selected decks.
            #
            wins = self.df.loc[self.valid_wr_rows]['Wins'].sum()
            total = wins + self.df.loc[self.valid_wr_rows]['Losses'].sum()
            wr = wins/total
            # return hv.Curve([(0.5, 0.5),(5.5, 0.5)], 'copies', label='50% wr').opts(color='k', line_dash='dotted')

            plots.extend([
                hv.Curve([(-0.5, 0.5),(4.5, 0.5)], 'copies', 'winrate', label='50% wr').opts(
                    color='k', 
                    line_dash='dotted',
                    toolbar=None, 
                    default_tools=[],
                ),
                hv.Curve([(-0.5, wr),(4.5, wr)], 'copies', 'winrate', label='Deck average').opts(
                    color='k', 
                    line_dash='dashed',
                    toolbar=None, 
                    default_tools=[],
                )
            ])
                    
            # Create line plot using HoloViews
            win_rate_plot = hv.Overlay(plots).opts(
                width=375,
                height=375,
                title=f"Win Rate: {card}",
                ylabel='Win Rate',
                xlabel='Number of Copies',
                xlim=(-0.5, 4.5),
                ylim=(-0.1, 1.1),
                toolbar=None,
                default_tools=[],
                active_tools=[],
                legend_position='bottom_left',
                legend_cols=4,
            )
        
            display.append(win_rate_plot)
        
        return hv.Layout(display).cols(1)

    @param.depends('df_winrates')
    def get_matchup_matrix(self):
        if self.meta_share:
            return pn.pane.HTML(
                make_combined_matchup_html(
                    self.ci_data, 
                    self.archetype_list, 
                    self.df_winrates,
                    self.df_wr_lower,
                    self.df_wr_upper,
                    self.meta_share,
                    self.cards_data, 
                    hover=True,
                    plot_width=150, 
                    labels_width=250
                ),
                stylesheets=[""".winrate-cell-container {
  display: inline-block;
}

.winrate-tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: #333;
  color: #fff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 1000;
  pointer-events: none;
  transition: opacity 0.15s ease-in-out;
  margin-bottom: 5px;
}

.winrate-tooltip::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: #333;
}

.winrate-cell-container:hover .winrate-tooltip,
.winrate-cell-container:active .winrate-tooltip {
  visibility: visible;
  opacity: 1;
}

/* Mobile-specific: tap to toggle */
@media (hover: none) {
  .winrate-cell-container.active .winrate-tooltip {
    visibility: visible;
    opacity: 1;
  }
}"""]
            )
        else:
            return pn.pane.Markdown(
                "No data available, please change the date filter."
            )

# Create the dashboard
#
def create_dashboard(df, res_df, X, vocabulary, oracleid_lookup, cards_data, cluster_map, clusters_id, archetype_list):
    analyzer = MTGAnalyzer(df, res_df, X, vocabulary, oracleid_lookup, cards_data, cluster_map, clusters_id, archetype_list)
    
    # Create card selection widget
    #
    card_select = pn.widgets.MultiChoice(
        name='Required Cards',
        options=analyzer.card_options,
        value=[],
        placeholder='Search for cards...',
        # sizing_mode='stretch_width'
    )

    # Create card selection widget
    #
    card_exclude = pn.widgets.MultiChoice(
        name='Excluded Cards',
        options=analyzer.card_options,
        value=[],
        placeholder='Search for cards...',
        # sizing_mode='stretch_width'
    )
    
    initial_date_range = (df['Date'].max() - pd.Timedelta(weeks=3*4), df['Date'].max())
    # Create date range selector
    #
    date_range = pn.widgets.DateRangeSlider(
        name='Date Range',
        start=df['Date'].min(),
        end=df['Date'].max(),
        value=initial_date_range,
        sizing_mode='stretch_width'
    )

    # Create archetype selector
    #
    selected_archetype = HTMLRadioIconGroup(
        options=list(analyzer.clusters_id),
        html_options=[make_card_stack(
            a.split('\n'), 
            analyzer.cards_data, 
            hover=True,
            fix_width=100, 
            show_mana=False,
            font_size='7px',
        ) for a in analyzer.archetype_list],
        name='Archetype Selection',
        value=None,
        sizing_mode='stretch_width'
    )
    
    # Create card analysis widgets
    #
    card_analysis = pn.widgets.MultiChoice(
        name='Analyze Card',
        options=analyzer.card_options,
        value=[],
        placeholder='Search for cards...',
        sizing_mode='stretch_width'
    )
    
    # Link widgets to analyzer parameters
    #
    card_select.link(analyzer, value='selected_cards')
    card_exclude.link(analyzer, value='excluded_cards')
    card_analysis.link(analyzer, value='selected_analyze_card')
    date_range.link(analyzer, value='date_range')
    selected_archetype.link(analyzer, value='selected_archetype')



    description = pn.pane.HTML(
        '''
        Urza's Research Desk brought to you by me, <a target="_blank" rel="noopener noreferrer" href="https://bsky.app/profile/arckaynine.bsky.social">ArcKayNine</a>.<br>
        All data comes courtesy of the excellent work done by <a target="_blank" rel="noopener noreferrer" href="https://github.com/fbettega/MTG_decklistcache.git">fbettega</a>, built upon work by Badaro and others.<br>
        For more of my work, check out my blog, <a target="_blank" rel="noopener noreferrer" href="https://compulsiveresearchmtg.blogspot.com">CompulsiveResearchMtg</a> or the exploits of my team, <a href="https://bsky.app/profile/busstop-mtg.bsky.social">Team Bus Stop</a>.<br>
        If you find this useful, valuable, or interesting, consider supporting further work via my <a target="_blank" rel="noopener noreferrer" href="https://ko-fi.com/arckaynine">Ko-fi</a>.<br>
        Urza's Research Desk is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.<br>
        ''',
    )
    
    def clear_selections(event):
        with param.parameterized.batch_call_watchers(analyzer):
            card_select.value = analyzer.param.selected_cards.default
            card_exclude.value = analyzer.param.excluded_cards.default
            card_analysis.value = analyzer.param.selected_analyze_card.default
            date_range.value = initial_date_range
            selected_archetype.value = None
        
    reset_button = pn.widgets.Button(name='Reset filter')#, button_type='primary')
    reset_button.on_click(clear_selections)

    # Create layout groups
    #

    # Controls
    #
    controls = pn.Column(
        pn.pane.Markdown("""
## Brought to you by:
"""),
        pn.Row(
            pn.pane.PNG(
                Path(__file__).parent / "resources/MTG_Bazaar_LOGO_PNG-02.png",
                sizing_mode='scale_width'
            ),
            pn.pane.PNG(
                Path(__file__).parent / "resources/team_bus_stop_full_colour.png",
                sizing_mode='scale_width'
            )
        ),
        date_range,
        reset_button,
        description,
        sizing_mode='stretch_width'
    )

    archetype_drill_down_controls = pn.Column(
        analyzer.get_selection_info,
        pn.Tabs(
            pn.Column(
                selected_archetype,
                name="Filter by archetype"
            ),
            pn.Column(
                card_select,
                card_exclude,
                name="Filter by card"
            )
        ),
        sizing_mode='fixed',
        width=250,
    )

    # Views
    #
    aggregate_view = pn.Column(
        analyzer.get_deck_view,
        sizing_mode='stretch_both',
        name='Aggregate Deck Analysis'
    )
    
    analysis_view = pn.Column(
        card_analysis,
        pn.Row(
            analyzer.get_card_analysis,
            analyzer.get_winrate_analysis,
        ),
        sizing_mode='stretch_both',
        name='Card Performance Analysis'
    )

    drill_down_view = pn.Row(
        archetype_drill_down_controls,
        pn.Spacer(width=5),
        pn.Tabs(
            aggregate_view,
            analysis_view,
        ),
        name="Archetype Investigation",
        sizing_mode="stretch_both",
    )
    
    # Create template
    #
    template = pn.template.FastListTemplate(
        title="Urza's Research Desk",
        sidebar=[controls],
        main=[
            pn.Tabs(
                drill_down_view,
                pn.Column(analyzer.get_matchup_matrix, name="Matchup Matrix"),
                # TODO
                # Temporal analysis (moving average population + wr)
                sizing_mode='stretch_both',
                dynamic=True, # Only render the active tab.
            ),
        ],
        theme_toggle=False,
        sidebar_width=280,
    )
    
    return template


if __name__ == '__main__':
    df, X, res_df, vocabulary, oracleid_lookup, cards_data, cluster_map, clusters_id, archetype_list = load_data()
    dashboard = create_dashboard(df, res_df, X, vocabulary, oracleid_lookup, cards_data, cluster_map, clusters_id, archetype_list)
    dashboard.servable()