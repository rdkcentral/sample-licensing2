struct rb_node {
    unsigned long  __rb_parent_color;
    struct rb_node *rb_right;
    struct rb_node *rb_left;
} __attribute__((aligned(sizeof(long))));

struct rb_root {
    struct rb_node *rb_node;
};

#define RB_RED      0
#define RB_BLACK    1
#define rb_parent(r)   ((struct rb_node *)((r)->__rb_parent_color & ~3))

static void __rb_rotate_left(struct rb_node *node, struct rb_root *root) {
    struct rb_node *right = node->rb_right;
    struct rb_node *parent = rb_parent(node);
    if ((node->rb_right = right->rb_left))
        right->rb_left->__rb_parent_color = (unsigned long)node | (right->rb_left->__rb_parent_color & 1);
    right->rb_left = node;
    right->__rb_parent_color = (unsigned long)parent | (right->__rb_parent_color & 1);
    if (parent) {
        if (node == parent->rb_left)
            parent->rb_left = right;
        else
            parent->rb_right = right;
    } else
        root->rb_node = right;
    node->__rb_parent_color = (unsigned long)right | (node->__rb_parent_color & 1);
}
