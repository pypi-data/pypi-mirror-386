import numpy as np
import pandas as pd

from scipy.stats import binomtest
# from scipy import sparse

from sklearn.cluster import AgglomerativeClustering
from tqdm import tqdm

def simple_threshold_clustering(X, distance_threshold, metric='manhattan'):
    """
    Simple single-pass clustering based on distance threshold.
    
    For each point, we check if it's within the threshold distance of any
    existing cluster. If so, we add it to that cluster. If not, we create
    a new cluster.
    
    This is effectively single-linkage clustering with a distance threshold,
    but implemented as a greedy single-pass algorithm.
    
    Time complexity: O(n * k) where k is the number of clusters (often << n)
    Space complexity: O(n + k)
    
    Parameters:
    -----------
    X : sparse matrix or dense array, shape (n_samples, n_features)
        The input data
    distance_threshold : float
        Maximum distance for points to be in the same cluster
    metric : str, default='manhattan'
        Distance metric to use
        
    Returns:
    --------
    labels : array, shape (n_samples,)
        Cluster labels for each point
    """
    n_samples = X.shape[0]

    print('starting greedy clustering')
    
    # # Convert to dense if sparse for easier indexing
    # # For very large sparse matrices, you might want to keep sparse
    # # and use sparse-aware distance computation
    # if hasattr(X, 'toarray'):
    #     X_dense = X.toarray()
    # else:
    #     X_dense = X
    
    def manhattan_distance(i, j):
        """Compute Manhattan distance between two points"""
        return np.sum(np.abs(i - j))
    
    # Initialize clusters
    labels = np.full(n_samples, -1)  # -1 means unassigned
    cluster_representatives = []  # Store one representative point per cluster
    cluster_sizes = []
    next_cluster_id = 0
    
    # Process each point
    for i in tqdm(range(n_samples)):
        assigned = False
        
        # Check distance to each existing cluster (via its representative)
        for cluster_id in range(next_cluster_id):
            rep_point = cluster_representatives[cluster_id] / cluster_sizes[cluster_id]
            if manhattan_distance(X[i], rep_point) <= distance_threshold:
                # Assign to this cluster
                labels[i] = cluster_id
                cluster_sizes[cluster_id] += 1
                cluster_representatives[cluster_id] += X[i]
                assigned = True
                break  # Take first cluster that's close enough
        
        # If not assigned to any existing cluster, create a new one
        if not assigned:
            labels[i] = next_cluster_id
            cluster_representatives.append(X[i])  # Use this point as representative
            cluster_sizes.append(1)
            next_cluster_id += 1
    
    return labels

def generate_archetypes(X, cards_data, vocabulary, n_cards=4, remove_pct=1):

    # Most other uses need the vocabulary, we need the inverse here though.
    #
    vocabulary_inv = {v:k for k, v in vocabulary.items() if k is not None}

    # if X.shape[0] >= 5000:
    #     cluster_labels_raw = simple_threshold_clustering(X, 60)

    # else:

    # Control granularity with distance_threshold or n_clusters
    agg_clustering = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=40,  # Adjust this for granularity
        metric='manhattan',
        linkage='single'
    )

    print('clustering...')
    print(f'{X.shape=}, {len(vocabulary)}')
    if X.shape[0] > 2000:
        cluster_labels_raw = agg_clustering.fit_predict(X[-2000:].toarray()).astype(str)
        del agg_clustering

        unique_values, _ = np.unique(cluster_labels_raw, return_counts=True)

        cluster_centers = np.array([
            np.mean(X[-2000:][cluster_labels_raw == c], axis=0) for c in unique_values
        ]).reshape(
            (len(unique_values), len(vocabulary))
        )

        other_labels = list()
        # print(unique_values)

        next_label = len(unique_values) + 1

        print(cluster_centers.shape)

        for i in range(X.shape[0]-2000):
            dists = np.sum(np.abs(cluster_centers - X[i].toarray()), axis=1)
            if any(dists<=40):
                other_labels.append(unique_values[np.argmax(dists<=40)])
            else:
                other_labels.append(str(next_label))
                next_label += 1

        cluster_labels_raw = np.concat([np.array(other_labels), cluster_labels_raw], axis=None)

    else:
        cluster_labels_raw = agg_clustering.fit_predict(X.toarray()).astype(str)
        del agg_clustering

    print('done')

    unique_values, counts = np.unique(cluster_labels_raw, return_counts=True)
    to_remove = unique_values[counts<X.shape[0]*remove_pct/100] # Remove decks with <remove_pct%

    deck_archetypes = cluster_labels_raw
    deck_archetypes[np.isin(cluster_labels_raw, to_remove)] = '-1'

    unique_values, counts = np.unique(deck_archetypes, return_counts=True)
    clusters_count, clusters_id = zip(*sorted(zip(counts, unique_values), reverse=True))

    cluster_map = {'-1':'Other'}

    overall_means = np.array(X.mean(axis=0)).flatten()

    for i in clusters_id:
        if i != '-1':
            cluster_mask = deck_archetypes == i
            cluster_decks = X[cluster_mask]
            cluster_decks.data = np.clip(cluster_decks.data, 0, 4)
            card_frequencies = np.array((cluster_decks > 0).mean(axis=0)).flatten() # Proportion of decks playing each card
            weighted_scores = np.array(cluster_decks.mean(axis=0)).flatten() * card_frequencies

            cluster_means = np.array(cluster_decks.mean(axis=0)).flatten()
            

            # Apply land penalty if needed
            land_penalty = np.array(
                [
                    0.5 if 'Land' in cards_data.get(
                        vocabulary_inv.get(idx).replace('_SB',''),[{'types':[]}]
                    )[0]['types'] else 1.0 for idx in range(X.shape[1])
                ]
            )
            card_frequencies *= land_penalty
            distinctiveness = (cluster_means / (overall_means + 1e-8)) * land_penalty

            combined_scores = weighted_scores * distinctiveness

            # Get sorted indices for each category
            representative = np.argsort(combined_scores)[::-1][:n_cards]

            cluster_map[i] = '\n'.join([vocabulary_inv.get(a).replace('_SB','') for a in representative])
            # cluster_map[i] = make_card_stack([vocabulary_inv.get(a).replace('_SB','') for a in representative], cards_data)

    archetype_list = list(map(cluster_map.get, list(clusters_id)))
    return cluster_map, clusters_id, archetype_list, deck_archetypes

def make_matchup_matrix(df, res_df, cluster_map, clusters_id, archetype_list):

    res_arch = pd.merge(
        res_df, df[['Player', 'Tournament', 'Archetype']], 
        left_on=['Player1', 'Tournament'], right_on=['Player', 'Tournament'],
    )
    res_arch = pd.merge(
        res_arch, df[['Player', 'Tournament', 'Archetype']], 
        left_on=['Player2', 'Tournament'], right_on=['Player', 'Tournament'], 
        suffixes = ('_W','_L')
    )

    # Win counts matrix (W vs L)
    #
    df_wins = pd.crosstab(
        res_arch['Archetype_W'], res_arch['Archetype_L'], margins=False
    ).reindex(
        index=list(clusters_id), columns=list(clusters_id), fill_value=0  # Add fill_value
    ).rename(
        columns=cluster_map, index=cluster_map
    ).reindex(
        index=archetype_list, columns=archetype_list, fill_value=0  # Reindex again to ensure all archetypes present
    )

    # Loss counts matrix (L vs W) - transpose the matchup
    #
    df_losses = pd.crosstab(
        res_arch['Archetype_L'], res_arch['Archetype_W'], margins=False
    ).reindex(
        index=list(clusters_id), columns=list(clusters_id), fill_value=0  # Add fill_value
    ).rename(
        columns=cluster_map, index=cluster_map
    ).reindex(
        index=archetype_list, columns=archetype_list, fill_value=0  # Reindex again to ensure all archetypes present
    )

    # Combine for total games and win percentages
    df_matches = df_wins.add(df_losses, fill_value=0)
    df_winrates = df_wins.div(df_matches, fill_value=0)

    # --- Compute confidence intervals for each matchup ---
    df_lower = pd.DataFrame(index=df_winrates.index, columns=df_winrates.columns)
    df_upper = pd.DataFrame(index=df_winrates.index, columns=df_winrates.columns)

    for deck in df_winrates.index:
        for opponent in df_winrates.columns:
            wins = df_wins.loc[deck, opponent] if deck in df_wins.index and opponent in df_wins.columns else 0
            total = df_matches.loc[deck, opponent] if deck in df_matches.index and opponent in df_matches.columns else 0
            
            if pd.notna(total) and total > 0:
                ci = binomtest(int(round(wins)), n=int(total)).proportion_ci(confidence_level=0.95)
                df_lower.loc[deck, opponent] = ci.low
                df_upper.loc[deck, opponent] = ci.high
            else:
                df_lower.loc[deck, opponent] = np.nan
                df_upper.loc[deck, opponent] = np.nan

    # Convert to float type
    df_lower = df_lower.astype(float)
    df_upper = df_upper.astype(float)

    # --- Aggregate wins and matches ---
    archetype_wins = (df_winrates * df_matches).sum(axis=1)
    archetype_matches = df_matches.sum(axis=1)

    # --- Compute binomial confidence intervals ---
    ci_data = []
    for archetype in archetype_list:
        wins = archetype_wins.get(archetype, 0)
        total = archetype_matches.get(archetype, 0)

        if total > 0:
            ci = binomtest(int(round(wins)), n=total).proportion_ci(confidence_level=0.95)
            win_rate = wins / total
            ci_data.append((win_rate, archetype, win_rate - ci.low, ci.high - win_rate))
        else:
            ci_data.append((np.nan, archetype, np.nan, np.nan))

    return ci_data, df_winrates, df_lower, df_upper
