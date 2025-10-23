/*
 * Copyright (C) 2023 Dominik Drexler and Simon Stahlberg
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef MIMIR_SEARCH_ALGORITHMS_HPP_
#define MIMIR_SEARCH_ALGORITHMS_HPP_

/**
 * Include all specializations here
 */

#include "mimir/search/algorithms/astar_eager.hpp"
#include "mimir/search/algorithms/astar_eager/event_handlers.hpp"
#include "mimir/search/algorithms/astar_lazy.hpp"
#include "mimir/search/algorithms/astar_lazy/event_handlers.hpp"
#include "mimir/search/algorithms/brfs.hpp"
#include "mimir/search/algorithms/brfs/event_handlers.hpp"
#include "mimir/search/algorithms/gbfs_eager.hpp"
#include "mimir/search/algorithms/gbfs_eager/event_handlers.hpp"
#include "mimir/search/algorithms/gbfs_lazy.hpp"
#include "mimir/search/algorithms/gbfs_lazy/event_handlers.hpp"
#include "mimir/search/algorithms/iw.hpp"
#include "mimir/search/algorithms/iw/event_handlers.hpp"
#include "mimir/search/algorithms/siw.hpp"
#include "mimir/search/algorithms/siw/event_handlers.hpp"

#endif
