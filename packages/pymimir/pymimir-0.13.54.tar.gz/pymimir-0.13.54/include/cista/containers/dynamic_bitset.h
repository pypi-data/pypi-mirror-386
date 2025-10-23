#pragma once

#include "cista/bit_counting.h"
#include "cista/containers/vector.h"
#include "cista/hash.h"

#include <bit>
#include <cassert>
#include <cinttypes>
#include <iosfwd>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>

namespace cista
{

template<typename Block, template<typename> typename Ptr>
struct basic_dynamic_bitset
{
    using block_type = Block;

    static constexpr std::size_t block_size = sizeof(Block) * 8;
    // Compile-time check to ensure block_size is a power of two
    static_assert((block_size & (block_size - 1)) == 0, "Error: Block size must be a power of two.");

    static constexpr std::size_t block_size_log2 = std::bit_width(block_size) - 1;
    // 000...
    static constexpr Block block_zeros = 0;
    // 111...
    static constexpr Block block_ones = Block(-1);
    // 100...
    static constexpr Block block_msb_one = Block(1) << (block_size - 1);
    // 011...
    static constexpr Block block_msb_zero = block_ones & (~block_msb_one);
    // 111...
    static constexpr std::size_t no_position = std::size_t(-1);

    static constexpr size_t get_index(size_t position) noexcept { return position >> block_size_log2; }

    static constexpr size_t get_offset(size_t position) noexcept { return position & (block_size - 1); }

    static constexpr size_t get_lsb_position(Block n) noexcept
    {
        assert(n != 0);
        const Block v = n & (-n);
        return std::bit_width(v) - 1;  // bit_width uses more efficient specialized cpu instructions
    }

    /**
     * Constructors
     */

    constexpr basic_dynamic_bitset() noexcept = default;

    constexpr basic_dynamic_bitset(size_t num_bits) : blocks_((num_bits / block_size) + 1) {}

    constexpr basic_dynamic_bitset(const basic_dynamic_bitset& other) : blocks_(other.blocks_) {}

    constexpr basic_dynamic_bitset& operator=(const basic_dynamic_bitset& other)
    {
        if (this != &other)
        {
            blocks_ = other.blocks_;
        }
        return *this;
    }

    /**
     * Operators
     */

    friend constexpr bool operator==(const basic_dynamic_bitset& lhs, const basic_dynamic_bitset& rhs)
    {
        if (&lhs != &rhs)
        {
            std::size_t common_size = std::min(lhs.blocks_.size(), rhs.blocks_.size());
            if (std::memcmp(lhs.blocks_.data(), rhs.blocks_.data(), common_size * sizeof(Block)) != 0)
                return false;

            std::size_t max_size = std::max(lhs.blocks_.size(), rhs.blocks_.size());

            for (std::size_t index = common_size; index < max_size; ++index)
            {
                auto this_value = index < lhs.blocks_.size() ? lhs.blocks_[index] : block_zeros;
                auto other_value = index < rhs.blocks_.size() ? rhs.blocks_[index] : block_zeros;

                if (this_value != other_value)
                {
                    return false;
                }
            }

            return true;
        }

        return true;
    }

    /**
     * Iterators
     */

    class const_iterator
    {
    private:
        const Block* blocks_;
        size_t num_blocks_;
        size_t current_block_;
        size_t current_pos_;
        Block current_block_state_;

        constexpr void advance()
        {
            while (current_block_ < num_blocks_)
            {
                // Find next set bit in this block
                if (current_block_state_)
                {
                    // Extract the index of the next set bit
                    size_t bit_index = get_lsb_position(current_block_state_);
                    current_pos_ = (current_block_ << block_size_log2) + bit_index;

                    // Clear this bit
                    current_block_state_ &= (current_block_state_ - 1);

                    return;
                }

                ++current_block_;
                if (current_block_ < num_blocks_)
                {
                    current_block_state_ = blocks_[current_block_];
                }
            }
            current_pos_ = no_position;
        }

    public:
        using difference_type = int;
        using value_type = uint32_t;
        using pointer = uint32_t*;
        using reference = uint32_t&;
        using iterator_category = std::forward_iterator_tag;
        using iterator_concept = std::forward_iterator_tag;

        constexpr const_iterator() : blocks_(nullptr), num_blocks_(0), current_block_(0), current_pos_(no_position) {}
        constexpr const_iterator(const Block* blocks, size_t num_blocks, bool begin) :
            blocks_(blocks),
            num_blocks_(num_blocks),
            current_block_(begin ? 0 : num_blocks),
            current_pos_(no_position),
            current_block_state_(num_blocks > 0 ? blocks[0] : 0)
        {
            if (begin && num_blocks_ > 0)
            {
                advance();
            }
        }

        constexpr size_t operator*() const { return current_pos_; }
        constexpr const_iterator& operator++()
        {
            if (current_pos_ != no_position)
            {
                advance();
            }
            return *this;
        }
        constexpr const_iterator operator++(int)
        {
            const_iterator tmp = *this;
            ++(*this);
            return tmp;
        }
        constexpr const_iterator operator+(size_t n) const
        {
            const_iterator tmp = *this;
            tmp += n;
            return tmp;
        }
        constexpr const_iterator& operator+=(size_t n)
        {
            for (size_t i = 0; i < n; ++i)
            {
                advance();
            }
            return *this;
        }
        constexpr bool operator==(const const_iterator& other) const { return current_pos_ == other.current_pos_; }
        constexpr bool operator!=(const const_iterator& other) const { return !(*this == other); }
    };

    constexpr const_iterator begin() const { return const_iterator(blocks_.data(), blocks_.size(), true); }

    constexpr const_iterator end() const { return const_iterator(blocks_.data(), blocks_.size(), false); }

    /**
     * Utility
     */

    /// @brief Shrink the bitset to minimum number of blocks to represent its bits.
    constexpr void shrink_to_fit()
    {
        int32_t last_non_default_block_index = blocks_.size() - 1;

        for (; last_non_default_block_index >= 0; --last_non_default_block_index)
        {
            if (blocks_[last_non_default_block_index] != block_zeros)
            {
                break;
            }
        }

        blocks_.resize(last_non_default_block_index + 1);
    }

    constexpr void resize_to_fit(const basic_dynamic_bitset& other)
    {
        if (blocks_.size() < other.blocks_.size())
        {
            blocks_.resize(other.blocks_.size(), block_zeros);
        }
    }

    constexpr std::size_t next_set_bit(std::size_t position) const
    {
        std::size_t index = get_index(position);
        std::size_t offset = get_offset(position);

        for (auto iter = blocks_.begin() + index; iter < blocks_.end(); ++iter)
        {
            // Shift so that we start checking from the offset
            const Block value = *iter >> offset;

            if (value)
            {
                // If there are set bits in the current value
                const auto lsb_position = get_lsb_position(value);
                return (index << block_size_log2) + offset + lsb_position;
            }

            // Reset offset for the next value
            offset = 0;
        }

        return no_position;
    }

    /**
     * Bit fiddeling
     */

    constexpr bool get(std::size_t position) const
    {
        const std::size_t index = get_index(position);
        const std::size_t offset = get_offset(position);

        return (index < blocks_.size()) ? ((blocks_[index] & (static_cast<Block>(1) << offset)) != 0) : 0;
    }

    /// @brief Set a bit at a specific position
    /// @param position
    constexpr void set(std::size_t position)
    {
        const std::size_t index = get_index(position);
        const std::size_t offset = get_offset(position);

        if (index >= blocks_.size())
        {
            blocks_.resize(index + 1, block_zeros);
        }

        blocks_[index] |= (static_cast<Block>(1) << offset);  // Set the bit at the offset
    }

    constexpr void set_all(size_t num_bits, bool value = false)
    {
        blocks_.clear();

        if (num_bits == 0)
            return;

        const size_t last_bit = num_bits - 1;
        const size_t required_blocks = get_index(last_bit) + 1;
        const size_t offset = get_offset(last_bit);

        blocks_.resize(required_blocks - 1, value ? block_ones : block_zeros);
        Block last = value ? ((offset == block_size - 1) ? block_ones : ((Block(1) << (offset + 1)) - 1)) : block_zeros;
        blocks_.emplace_back(last);
    }

    /// @brief Unset a bit at a specific position
    /// @param position
    constexpr void unset(std::size_t position)
    {
        const std::size_t index = get_index(position);
        const std::size_t offset = get_offset(position);

        if (index >= blocks_.size())
        {
            blocks_.resize(index + 1, block_zeros);
        }

        blocks_[index] &= ~(static_cast<Block>(1) << offset);  // Set the bit at the offset
    }

    /// @brief Unset all bits and shrink its size to represent the bits
    constexpr void unset_all() { blocks_.clear(); }

    /**
     * Bitset operations
     */

    constexpr basic_dynamic_bitset& operator~()
    {
        for (Block& value : blocks_)
        {
            value = ~value;
        }
        shrink_to_fit();

        return *this;
    }

    constexpr void negate(size_t num_bits)
    {
        if (num_bits == 0)
            return;

        const size_t last_bit = num_bits - 1;
        const size_t index = get_index(last_bit);
        const size_t offset = get_offset(last_bit);

        // Resize to fit negated atoms.
        blocks_.resize(index + 1, block_zeros);

        ~(*this);

        // Mask out extra bits in the last block
        if (offset < block_size - 1)
        {
            Block& last_block = blocks_.back();
            Block mask = (Block(1) << (offset + 1)) - 1;
            last_block &= mask;
        }
    }

    constexpr basic_dynamic_bitset operator|(const basic_dynamic_bitset& other) const
    {
        auto result = basic_dynamic_bitset(*this);
        result |= other;

        return result;
    }

    constexpr basic_dynamic_bitset& operator|=(const basic_dynamic_bitset& other)
    {
        // Update blocks
        resize_to_fit(other);
        // Other blocks might still be smaller which is fine
        assert(other.blocks_.size() <= blocks_.size());

        auto it = blocks_.begin();
        auto other_it = other.blocks_.begin();
        // Since other is potentially smaller, it acts as termination conditions
        while (other_it != other.blocks_.end())
        {
            *it |= *other_it;
            ++it;
            ++other_it;
        }

        return *this;
    }

    constexpr basic_dynamic_bitset operator^(const basic_dynamic_bitset& other) const
    {
        auto result = basic_dynamic_bitset(*this);
        result ^= other;

        return result;
    }

    constexpr basic_dynamic_bitset& operator^=(const basic_dynamic_bitset& other)
    {
        // Update blocks
        resize_to_fit(other);
        // Other blocks might still be smaller which is fine
        assert(other.blocks_.size() <= blocks_.size());

        auto it = blocks_.begin();
        auto other_it = other.blocks_.begin();
        while (other_it != other.blocks_.end())
        {
            *it ^= *other_it;
            ++it;
            ++other_it;
        }

        return *this;
    }

    constexpr basic_dynamic_bitset operator&(const basic_dynamic_bitset& other) const
    {
        auto result = basic_dynamic_bitset(*this);
        result &= other;

        return result;
    }

    constexpr basic_dynamic_bitset& operator&=(const basic_dynamic_bitset& other)
    {
        // Update blocks
        resize_to_fit(other);
        // Other blocks might still be smaller which is fine
        assert(other.blocks_.size() <= blocks_.size());

        auto it = blocks_.begin();
        auto other_it = other.blocks_.begin();
        while (other_it != other.blocks_.end())
        {
            *it &= *other_it;
            ++it;
            ++other_it;
        }
        // Shrink to size of other since those bits should become default valued
        blocks_.resize(other.blocks_.size());

        return *this;
    }

    constexpr basic_dynamic_bitset operator-(const basic_dynamic_bitset& other) const
    {
        auto result = basic_dynamic_bitset(*this);
        result -= other;

        return result;
    }

    constexpr basic_dynamic_bitset& operator-=(const basic_dynamic_bitset& other)
    {
        // Update blocks
        resize_to_fit(other);
        // Other blocks might still be smaller which is fine
        assert(other.blocks_.size() <= blocks_.size());

        auto it = blocks_.begin();
        auto other_it = other.blocks_.begin();
        while (other_it != other.blocks_.end())
        {
            *it &= ~(*other_it);
            ++it;
            ++other_it;
        }
        // The remaining blocks stay the same.

        return *this;
    }

    constexpr bool is_superseteq(const basic_dynamic_bitset& other) const
    {
        std::size_t common_size = std::min(blocks_.size(), other.blocks_.size());

        for (std::size_t index = 0; index < common_size; ++index)
        {
            if ((blocks_[index] & other.blocks_[index]) != other.blocks_[index])
            {
                // There exists a set bit in other block that is not set in block.
                return false;
            }
        }

        if (other.blocks_.size() <= blocks_.size())
        {
            // blocks can only contain additional set bits
            return true;
        }

        for (std::size_t index = common_size; index < other.blocks_.size(); ++index)
        {
            if (other.blocks_[index])
            {
                // other_block contains additional set bits
                return false;
            }
        }

        return true;
    }

    constexpr bool are_disjoint(const basic_dynamic_bitset& other) const
    {
        std::size_t common_size = std::min(blocks_.size(), other.blocks_.size());

        for (std::size_t index = 0; index < common_size; ++index)
        {
            if ((blocks_[index] & other.blocks_[index]) > 0)
            {
                // block and other_block have set bits in common
                return false;
            }
        }

        return true;
    }

    /**
     * Accessors
     */

    constexpr bool any() const
    {
        return std::any_of(blocks_.begin(), blocks_.end(), [](auto&& arg) { return arg != 0; });
    }

    constexpr size_t count() const
    {
        size_t count = 0;
        for (auto it = begin(); it != end(); ++it)
        {
            ++count;
        }
        return count;
    }

    const cista::basic_vector<Block, Ptr>& blocks() const { return blocks_; }

    cista::basic_vector<Block, Ptr> blocks_ {};
};

namespace raw
{
template<typename Block>
using dynamic_bitset = basic_dynamic_bitset<Block, ptr>;
}

namespace offset
{
template<typename Block>
using dynamic_bitset = basic_dynamic_bitset<Block, ptr>;
}

}  // namespace cista
